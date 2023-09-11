import bpy
import bmesh
import math

from mathutils import Vector
from mathutils.bvhtree import BVHTree

from bpy_extras import view3d_utils

import gpu
import gpu_extras
from gpu_extras.presets import draw_circle_2d
from gpu_extras.batch import batch_for_shader


class NeoInteractiveUvEditor(bpy.types.Operator):
    bl_idname = "view3d.nuv_interactiveuveditor"
    bl_label = "Interactive Uv Editor"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self):
        # setup drawing data
        self.line_shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
        self.circle_shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")

        self.hit_result = None
        super().__init__()

    def modal(self, context, event):

        context.area.tag_redraw()

        # find component under mouse cursor
        if not self.dragging_uv:
            self.hit_result = self.try_hit_mesh(context, event)
            self.try_assign_face()
            self.find_edit_components()

        # handle UV dragging
        if self.warped_mouse:
            self.warped_mouse = False
            self.mouse_prev_x = event.mouse_x
            self.mouse_prev_y = event.mouse_y
        else:
            self.mouse_prev_x = self.mouse_x
            self.mouse_prev_y = self.mouse_y

        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y

        self.mouse_delta_x = self.mouse_x - self.mouse_prev_x
        self.mouse_delta_y = self.mouse_y - self.mouse_prev_y

        if self.dragging_uv: self.update_uvs(context)

        if event.type == "LEFTMOUSE":
            if event.value == "PRESS" and not self.dragging_uv:
                self.dragging_uv = True
                self.active_component = self.edit_component

            if event.value == "RELEASE" and self.dragging_uv:
                self.dragging_uv = False
                self.active_component = None

        # user exit
        if event.type == "RIGHTMOUSE" and not self.dragging_uv:
            self.finished()
            return {"FINISHED"}

        return {'RUNNING_MODAL'}

    def update_uvs(self, context):

        # mouse wrapping
        if self.mouse_x > context.area.x + context.area.width:
            context.window.cursor_warp(context.area.x, self.mouse_y)
            self.warped_mouse = True

        if self.mouse_x < context.area.x:
            context.window.cursor_warp(context.area.x + context.area.width, self.mouse_y)
            self.warped_mouse = True

        if self.mouse_y > context.area.y + context.area.height:
            context.window.cursor_warp(self.mouse_x, context.area.y)
            self.warped_mouse = True

        if self.mouse_y < context.area.y:
            context.window.cursor_warp(self.mouse_x, context.area.y + context.area.height)
            self.warped_mouse = True

        verts = []
        component = self.active_component

        if isinstance(component, bmesh.types.BMFace):
            for e in component.edges:
                for v in e.verts:
                    verts.append(v)
        elif isinstance(component, bmesh.types.BMEdge):
            for v in component.verts:
                verts.append(v)
        elif isinstance(component, bmesh.types.BMVert):
            verts.append(component)

        layer = self.edit_mesh.loops.layers.uv
        uv_layer = layer.verify()

        for v in verts:
            for l in v.link_loops:
                if l.face is not self.hit_face: continue # TODO: ADD OPTION TO DISABLE THIS

                l[uv_layer].uv += Vector((-self.mouse_delta_x, self.mouse_delta_y)) * 0.00001

        bmesh.update_edit_mesh(self.mesh, loop_triangles=False, destructive=False)


    def try_hit_mesh(self, context, event):
        mouse_pos = [event.mouse_region_x, event.mouse_region_y]
        region = bpy.context.region
        region_3d = bpy.context.region_data

        view_vec = view3d_utils.region_2d_to_vector_3d(region, region_3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, region_3d, mouse_pos)
        ray_target = ray_origin + view_vec

        self.mouse_world_loc = ray_origin

        matrix = self.obj.matrix_world.inverted()

        ray_origin_obj = matrix @ ray_origin
        ray_target_obj = matrix @ ray_target
        ray_dir_obj = ray_target_obj - ray_origin_obj

        result = self.tree.ray_cast(ray_origin_obj, ray_dir_obj)

        if result[0] is None: return None
        return result

    def try_assign_face(self):
        self.hit_face = None
        if self.hit_result is None: return

        #print(self.hit_result[2])
        self.hit_face = self.edit_mesh.faces[self.hit_result[2]]

    def find_edit_components(self):
        self.edit_component = None
        if self.hit_result is None: return
        if self.hit_face is None: return

        # start with face center
        self.edit_component = self.hit_face

        matrix = self.obj.matrix_world

        hit_point = matrix @ self.hit_result[0]
        face_center = matrix @ self.hit_face.calc_center_median()
        min_distance = (hit_point - face_center).magnitude

        # compare against edge centers
        for e in self.hit_face.edges:
            edge_center = matrix @ ((e.verts[0].co + e.verts[1].co) / 2.0)

            edge_distance = (hit_point - edge_center).magnitude
            if edge_distance < min_distance:
                min_distance = edge_distance
                self.edit_component = e

            # compare against edge vertices
            for v in e.verts:
                vertex_world = matrix @ v.co

                vert_distance = (hit_point - vertex_world).magnitude
                if vert_distance < min_distance:
                    min_distance = vert_distance
                    self.edit_component = v


    def finished(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.handle_v, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.handle_px, 'WINDOW')

    def on_update(self, context, event):
        pass

    @staticmethod
    def draw_callback_v(self, context):
        component = self.edit_component
        if component is not None:
            component_type = type(self.edit_component)

            world_matrix = self.obj.matrix_world

            if isinstance(component, bmesh.types.BMFace):
                self.draw_filled_face(component, world_matrix)
            elif isinstance(component, bmesh.types.BMEdge):
                self.line_shader.uniform_float("color", (1, 1, 0, 1))

                line_coords = [world_matrix @ component.verts[0].co, world_matrix @ component.verts[1].co]

                line_batch = batch_for_shader(self.line_shader, "LINES", {"pos": line_coords})
                line_batch.draw(self.line_shader)


    @staticmethod
    def draw_callback_px(self, context):
        region = bpy.context.region
        region_3d = bpy.context.space_data.region_3d

        world_matrix = self.obj.matrix_world

        component = self.edit_component

        if isinstance(component, bmesh.types.BMVert):
            viewport_coord = view3d_utils.location_3d_to_region_2d(region, region_3d, world_matrix @ component.co)
            self.draw_filled_circle(viewport_coord, 8.0, 10)
        pass

    def draw_filled_face(self, face, world_matrix):
        # wire
        self.line_shader.uniform_float("color", (1, 1, 0, 1))

        line_coords = []
        for e in face.edges:
            line_coords.append((world_matrix @ e.verts[0].co).to_tuple())
            line_coords.append((world_matrix @ e.verts[1].co).to_tuple())

        line_batch = batch_for_shader(self.line_shader, "LINES", {"pos": line_coords})
        line_batch.draw(self.line_shader)

    def draw_filled_circle(self, pos_2d, radius, segments):
        if segments < 3: return

        # wire
        self.circle_shader.uniform_float("color", (1, 1, 0, 1))

        verts = [pos_2d.to_tuple()]
        tris = []

        for i in range(0, segments + 1):
            rad = ((i + 1) / segments) * math.pi * 2.0

            x = (radius * math.cos(rad)) + pos_2d.x
            y = (radius * math.sin(rad)) + pos_2d.y

            verts.append((x, y))
            if i > 1:
                tris.append((0, i - 1, i))

            if i == segments - 1:
                tris.append((0, i, 1))


        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, "TRIS", {"pos": verts}, indices=tris)
        batch.draw(shader)

    def invoke(self, context, event):

        # make sure we're in edit mode
        t = bpy.context.object.type
        if t != "MESH": return {"FINISHED"}
        if bpy.context.active_object.mode != "EDIT": return {"FINISHED"}

        # init variables
        self.obj = bpy.context.object
        self.mesh = self.obj.data
        self.edit_mesh = bmesh.from_edit_mesh(self.mesh)
        self.tree = BVHTree.FromBMesh(self.edit_mesh, epsilon=0.1)
        self.hit_face = None
        self.edit_component = None

        self.active_component = None
        self.dragging_uv = False

        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_prev_x = 0
        self.mouse_prev_y = 0
        self.warped_mouse = False

        # setup handlers
        self.handle_v = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_v, (self, context), "WINDOW", "POST_VIEW")
        self.handle_px = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (self, context), "WINDOW", "POST_PIXEL")
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


classes = (
    NeoInteractiveUvEditor,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)