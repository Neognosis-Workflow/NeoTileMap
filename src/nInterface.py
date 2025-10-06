# region Imports

import bpy
import bmesh
import mathutils
from . import nMath
from . import nUv

# endregion

# region Settings

nuv_max_item_per_page = 20
nuv_preview_scale = 6.0

# endregion

# region Operators


class NeoUvUiSettings(bpy.types.PropertyGroup):
    settings_expanded: bpy.props.BoolProperty()
    tools_expanded: bpy.props.BoolProperty()
    rects_expanded: bpy.props.BoolProperty()

    correct_aspect_ratio: bpy.props.BoolProperty(default=True)
    snap_to_bounds: bpy.props.BoolProperty(default=False)

    unwrap_axis: bpy.props.IntVectorProperty(
        name="Unwrap Axis",
        min=-1,
        max=1,
        default=(0, 0, 1)
    )

    mode_space: bpy.props.EnumProperty(
        name="Unwrap Origins",
        items = (
            ("1", "Individual Face", "Individual Face"),
            ("2", "Center Of Selected", "Center Of Selected")
        ),
    )

    mode_unwrap: bpy.props.EnumProperty(
        name="Unwrap Mode",
        items=(
            ("1", "Face Is Up", "Face Is Up"),
            ("2", "World Is Up", "World Is Up"),
            ("3", "Object Is Up", "Object Is Up"),
            ("4", "Camera Is Up", "Camera Is Up"),
            ("5", "No Projection", "No Projection")
        ),
    )

    mode_rotate: bpy.props.EnumProperty(
        name= "Rotate Mode",
        items = (
            ("1", "Shift Array", "Shift Array"),
            ("2", "Orbit Verts", "Orbit Verts")
        ),
    )

    last_uv_set: bpy.props.IntProperty(
        name="Last Uv Set",
        default=-1
    )

    uv_editor_linked_faces: bpy.props.BoolProperty(
        name="Linked Uv Editing",
        default=False
    )

    uv_edit_pixel_snap: bpy.props.BoolProperty(
        name="Pixel Snap Uvs",
        default=True
    )


class UtilOpNeoUvUiFirstPage(bpy.types.Operator):
    bl_idname = "neo.uv_uifirstpage"
    bl_label = "First Page"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()
    
    def invoke(self, context, event):
        bpy.context.scene.nuv_uvSets[self.collectionIdx].page = 0
        return {'FINISHED'}


class UtilOpNeoUvUiNextPage(bpy.types.Operator):
    bl_idname = "neo.uv_uinextpage"
    bl_label = "Next Page"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()

    def invoke(self, context, event):
        items_len = len(bpy.context.scene.nuv_uvSets[self.collectionIdx].items)

        page = bpy.context.scene.nuv_uvSets[self.collectionIdx].page
        page += 1

        if page * nuv_max_item_per_page > items_len: page -= 1

        bpy.context.scene.nuv_uvSets[self.collectionIdx].page = page
        return {'FINISHED'}


class UtilOpNeoUvUiPrevPage(bpy.types.Operator):
    bl_idname = "neo.uv_uiprevpage"
    bl_label = "Previous Page"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()

    def invoke(self, context, event):
        page = bpy.context.scene.nuv_uvSets[self.collectionIdx].page
        page -= 1
        if page < 0: page = 0

        bpy.context.scene.nuv_uvSets[self.collectionIdx].page = page

        return {'FINISHED'}

# endregion

# region Interface Drawing


def ui_draw(layout, context):

    settings = bpy.context.scene.nuv_settings

    ui_draw_settings(layout, context, settings)
    ui_draw_manip_tools(layout, context, settings)
    ui_draw_rects(layout, context, settings)


def ui_draw_settings(layout, context, settings):
    """
    Draws the settings box for the panel.
    """

    # header
    container = layout.box()

    container.prop(settings, "settings_expanded", icon=get_expander_icon(settings.settings_expanded), emboss=False, text="Settings")
    if not settings.settings_expanded:
        return

    # aspect ratio
    container = container.box()

    c_row = container.row()
    c_row.split(factor=0.3)

    c_row.label(text="Unwrap Settings")

    c_col = c_row.column()
    c_col.prop(settings, "correct_aspect_ratio", expand=True, text="Correct Aspect Ratio")
    c_col.prop(settings, "snap_to_bounds", expand=True, text="Snap To Bounds")

    c_col.label(text="Unwrap Axis")
    c_row_inner = c_col.row()
    c_row_inner.prop(settings, "unwrap_axis", expand=True, text="")

    # space mode
    c_row = container.row()
    c_row.split(factor=0.3)

    c_row.label(text="Origins Mode")

    c_col = c_row.column()
    c_col.prop(settings, "mode_space", expand=True)

    # unwrap mode
    c_row = container.row()
    c_row.split(factor=0.3)

    c_row.label(text="Unwrap Mode")

    c_col = c_row.column()
    c_col.prop(settings, "mode_unwrap", expand=True)

    # rotate mode
    c_row = container.row()
    c_row.split(factor=0.3)

    c_row.label(text="Rotate Mode")

    c_col = c_row.column()
    c_col.prop(settings, "mode_rotate", expand=True)


def ui_draw_manip_tools(layout, context, settings):

    # header
    container = layout.box()

    container.prop(settings, "tools_expanded", icon=get_expander_icon(settings.tools_expanded), emboss=False, text="Tools")
    if not settings.tools_expanded:
        return

    container = container.box()

    # interactive uv tool
    if bpy.context.object.mode == "EDIT":
        container.operator("view3d.nuv_interactiveuveditor", text="Edit Uvs")
        c_row = container.row()
        c_row.split(factor=0.3)

        c_row.label(text="Edit Uvs Settings")

        c_col = c_row.column()
        c_col.prop(settings, "uv_editor_linked_faces")
        c_col.prop(settings, "uv_edit_pixel_snap")

    else:
        container.label(text="Enter edit mode to access Edit Uvs.")

    # rotate tool
    c_row = container.row()
    c_row.split(factor=0.3)

    c_row.label(text="Rotate")

    op = c_row.operator("neo.uv_rot", text="Left", icon="TRIA_LEFT")
    op.clockwise = False

    op = c_row.operator("neo.uv_rot", text="Right", icon="TRIA_RIGHT")
    op.clockwise = True

    # flip tool
    c_row = container.row()
    c_row.split(factor=0.3)

    c_row.label(text="Flip")

    op = c_row.operator("neo.uv_flip", text="U", icon="TRIA_RIGHT")
    op.horizontal = True

    op = c_row.operator("neo.uv_flip", text="V", icon="TRIA_UP")
    op.horizontal = False

    container.separator(factor=2)

    c_row = container.row()
    c_row.split(factor=0.3)
    c_row.label(text="Unwrap")

    c_row.operator("neo.uv_setuvrectnormal", text="Full Unwrap")
    c_row.operator("neo.uv_normalize", text="Normalize Selection")


def ui_draw_rects(layout, context, settings):

    # header
    container = layout.box()

    container.prop(settings, "rects_expanded", icon=get_expander_icon(settings.rects_expanded), emboss=False, text="Rect Sets")
    if not settings.rects_expanded:
        return

    container = container.box()
    max_items_per_row = round(context.region.width / (32 * nuv_preview_scale))

    collection_list = bpy.context.scene.nuv_uvSets
    for i in range(0, len(collection_list)):
        expanded = ui_draw_rect_list(collection_list[i], i, max_items_per_row, container, context)
        if expanded: container.separator(factor=1)


def ui_draw_rect_list(c, i, max_items_per_row, layout, context):

    # title
    row = layout.row()
    split = row.split(factor=0.9, align=True)

    split.prop(c, "expanded", icon=get_expander_icon(c.expanded), emboss=True, text=c.name)
    split.alert = True

    op = split.operator("neo.uvset_delete", icon="TRASH", text="")
    op.collectionIdx = i

    if not c.expanded:
        return False

    # rect actions
    layout = layout.box()
    items = c.items
    item_len = len(items)

    if c.relative_path:
        row = layout.row()
        split = row.split(factor=0.9)
        split.label(text=c.relative_path)

        op = split.operator("neo.uv_uireload", text="", icon="FILE_REFRESH")
        op.collectionIdx = i

    op = layout.operator("view3d.nuv_set_uv_rect_selector", text="Select UV", icon="UV_FACESEL", emboss=True)
    op.collectionIdx = i

    # manual UV selector
    layout.prop(c, "items_expanded", icon=get_expander_icon(c.items_expanded), emboss=True, text="Rect List")

    if not c.items_expanded:
        return True

    layout = layout.box()
    row = layout.row()
    row.label(text="Page")
    op = row.operator("neo.uv_uiprevpage")
    op.collectionIdx = i

    op = row.operator("neo.uv_uinextpage")
    op.collectionIdx = i

    op = row.operator("neo.uv_uifirstpage")
    op.collectionIdx = i

    # calculate page range
    start = c.page * nuv_max_item_per_page
    if start > item_len - 1:
        start = item_len - 1

    end = start + nuv_max_item_per_page

    # draw selection interface
    image_box = layout.column()
    image_row = image_box.row()
    row_i = 0

    for j in range(start, end):
        if j > item_len - 1:
            break

        if row_i > max_items_per_row:
            row_i = 0
            image_row = image_box.row()

        item = items[j]

        # try to get preview image
        preview_image = get_image_by_name(item.previewName)
        if preview_image is None:
            continue

        if bpy.app.version[0] >= 3:
            preview_image.preview_ensure()

        # draw button grid
        col = image_row.column()
        col.template_icon(icon_value=preview_image.preview.icon_id, scale=nuv_preview_scale)

        op = col.operator("neo.uv_setuvrect", text="Apply")
        op.collectionIdx = i
        op.rectIdx = j

        row_i += 1
    return True


def get_image_by_name(n):
    """
    Returns an image based on its name.
    :param n: The name of the image to try and find.
    :return: Image data block.
    """
    for i in bpy.data.images:
        if i.name == n:
            return i

    return None


def get_expander_icon(toggled):
    """
    Returns the icon to use for expanders.
    """

    return "DOWNARROW_HLT" if toggled else "RIGHTARROW"


def get_expander_string(toggled, name):
    """
    Returns the string to use as the text for an expander.
    """

    expand_str = "Hide " if toggled else "Show "
    return expand_str + name

# endregion

# region Blender


classes = (
    NeoUvUiSettings,
    UtilOpNeoUvUiFirstPage,
    UtilOpNeoUvUiNextPage,
    UtilOpNeoUvUiPrevPage,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.nuv_settings = bpy.props.PointerProperty(type=NeoUvUiSettings)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

# endregion