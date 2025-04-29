import bgl
import bpy
import gpu
import gpu_extras.presets
from gpu_extras.batch import batch_for_shader

is_blender_4_or_greater = bpy.app.version[0] > 3

if is_blender_4_or_greater:
    shader_img = gpu.shader.from_builtin('IMAGE')
    shader_color = gpu.shader.from_builtin('UNIFORM_COLOR')
else:
    shader_img = gpu.shader.from_builtin('2D_IMAGE')
    shader_color = gpu.shader.from_builtin('2D_UNIFORM_COLOR')


def mouse_in_bounds(mouse_x, mouse_y, top_left, top_right, bottom_right, bottom_left):
    mouse_x_in_bounds = top_left.x < mouse_x < top_right.x
    mouse_y_in_bounds = bottom_left.y < mouse_y < top_left.y
    return mouse_x_in_bounds and mouse_y_in_bounds


def draw_image(image, verts, tex_coord, indices):
    if is_blender_4_or_greater:
        draw_image_blender_4(image, verts, tex_coord, indices)
    else:
        draw_image_blender_3(image, verts, tex_coord, indices)


def draw_image_blender_3(image, verts, tex_coord, indices):
    if image.gl_load():
        raise Exception()

    bgl.glEnable(bgl.GL_BLEND)
    batch = batch_for_shader(shader_img, 'TRIS', {"pos": verts, "texCoord": tex_coord}, indices=indices)

    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)

    shader_img.bind()
    shader_img.uniform_int("image", 0)
    batch.draw(shader_img)

    bgl.glDisable(bgl.GL_BLEND)


def draw_image_blender_4(image, verts, tex_coord, indices):
    gpu.state.blend_set("ALPHA")

    batch = batch_for_shader(shader_img, 'TRIS', {"pos": verts, "texCoord": tex_coord}, indices=indices)
    shader_img.bind()
    shader_img.uniform_sampler("image", image)
    batch.draw(shader_img)

    gpu.state.blend_set("NONE")


def draw_transformed_image(image, area_width, area_height, zoom, offset_x, offset_y):
    """
    Draws a transformed image and returns additional information about the transformation of the image.
    :param image: The image to draw.
    :param area_width: The width of the area that the image will be drawn in.
    :param area_height: The height of the area that the image will be drawn in.
    :param zoom: How far zoomed into the image we are.
    :param offset_x: How offset along X the image is.
    :param offset_y: How offset along Y the image is.
    :return: Array of img_aspect, quad_width, quad_height center_x, center_y, bottom_left, bottom_right, top_left and top_right
    """
    # calculate image size
    if is_blender_4_or_greater:
        res_x = image.width
        res_y = image.height
    else:
        img_res = image.size
        res_x = img_res[0]
        res_y = img_res[1]

    new_width = res_x
    new_height = res_y
    img_aspect = res_x / res_y

    if new_width > area_width or new_height < area_height:
        new_width = area_width
        new_height = new_width / img_aspect

    if new_height > area_height or new_width < area_width:
        new_height = area_height
        new_width = new_height * img_aspect

    quad_width = new_width * zoom
    quad_height = new_height * zoom

    # calculate position of image center
    center_x = area_width / 2
    center_y = area_height / 2

    # calculate image bounds
    bottom_left = ((center_x - quad_width / 2) + offset_x, (center_y - quad_height / 2) + offset_y)
    bottom_right = ((center_x + quad_width / 2) + offset_x, (center_y - quad_height / 2) + offset_y)
    top_left = ((center_x - quad_width / 2) + offset_x, (center_y + quad_height / 2) + offset_y)
    top_right = ((center_x + quad_width / 2) + offset_x, (center_y + quad_height / 2) + offset_y)

    # draw mesh
    verts = (
        bottom_left,
        bottom_right,
        top_left,
        top_right
    )

    texCoord = (
        (0, 0), (1, 0), (0, 1), (1, 1)
    )

    indices = (
        (0, 1, 2), (2, 1, 3)
    )

    draw_image(image, verts, texCoord, indices)
    return [img_aspect, quad_width, quad_height, center_x, center_y, bottom_left, bottom_right, top_left, top_right]


def line_draw(pos_a, pos_b, color):
    if is_blender_4_or_greater:
        line_draw_blender_4(pos_a, pos_b, color)
    else:
        line_draw_blender_3(pos_a, pos_b, color)


def line_draw_blender_4(pos_a, pos_b, color):
    line = (pos_a, pos_b)
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(2.0)

    batch = batch_for_shader(shader_color, 'LINES', {"pos": line})
    shader_color.bind()
    shader_color.uniform_float("color", color)
    batch.draw(shader_color)

    gpu.state.blend_set("NONE")
    gpu.state.line_width_set(1.0)


def line_draw_blender_3(pos_a, pos_b, color):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(2)

    line = (pos_a, pos_b)
    batch = batch_for_shader(shader_color, 'LINES', {"pos": line})
    shader_color.bind()
    shader_color.uniform_float("color", color)
    batch.draw(shader_color)

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)


def grid_sort(a, b):
    if b[0] < a[0] or b[1] < a[1]:
        return [b, a]
    else:
        return [a, b]


def find_closest_bound_vert(uv, top_left, top_right, bottom_right, bottom_left):
    to_top_left = (uv - top_left).magnitude
    to_top_right = (uv - top_right).magnitude
    to_bottom_right = (uv - bottom_right).magnitude
    to_bottom_left = (uv - bottom_left).magnitude

    bound_list = [top_left, top_right, bottom_left, bottom_right]
    dist_list = [to_top_left, to_top_right, to_bottom_left, to_bottom_right]

    chosen_distance = 0
    max_dist = float("infinity")
    for i in range(0, 4):
        if dist_list[i] < max_dist:
            max_dist = dist_list[i]
            chosen_distance = i

    return bound_list[chosen_distance]


def abs_uv(uv):
    uv[0] = (uv[0] + 1.0) / 2.0
    uv[1] = (uv[1] + 1.0) / 2.0
    return uv


def register():
    pass


def unregister():
    pass