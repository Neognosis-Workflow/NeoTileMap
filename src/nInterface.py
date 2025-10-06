# region Imports

import bpy
import bmesh
import mathutils
from . import nMath
from . import nUv

# endregion

# region Settings

nuv_sidebar_category = "Neognosis"
nuv_max_item_per_page = 20
nuv_preview_scale = 6.0
nuv_pattern_preview_scale = 5.0
nuv_settings_only = False

# endregion

# region Widgets


class NeoPatternList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", emboss=False, text="")

# endregion

# region Operators


class NeoSidebarPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_NeoTmPanel'
    bl_label = 'Neo Tile Map'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Neognosis'

    @classmethod
    def poll(self, context):
        if context.area.type == "VIEW_3D":
            return True

    def draw(self, context):
        layout = self.layout
        ui_draw(layout, context)
        return


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


def get_icon_value(name):
    items = bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.items()
    dict = {tup[1].identifier : tup[1].value for tup in items}

    return dict[name]


rect_missing_icon = get_icon_value("CANCEL")


def only_draw_settings_this_frame():
    global nuv_settings_only
    nuv_settings_only = True


def is_mouse_in_neognosis_sidebar(event):
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            sidebar_region = None
            for region in area.regions:
                if region.type == "UI":
                    sidebar_region = region
                    break

            if not sidebar_region:
                return False

            if sidebar_region.active_panel_category != NeoSidebarPanel.bl_category:
                return False

            x_min = region.x
            y_min = region.y
            x_max = region.x + region.width
            y_max = region.y + region.height
            return x_min < event.mouse_x < x_max and y_min < event.mouse_y < y_max


def ui_draw(layout, context):

    settings = bpy.context.scene.nuv_settings

    ui_draw_settings(layout, context, settings)

    global nuv_settings_only
    if nuv_settings_only:
        nuv_settings_only = False
        return

    if bpy.context.object is None:
        in_edit_mode = False
    else:
        in_edit_mode = bpy.context.object.mode == "EDIT"
    ui_draw_manip_tools(layout, context, settings, in_edit_mode)
    ui_draw_rects(layout, context, settings, in_edit_mode)


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


def ui_draw_manip_tools(layout, context, settings, in_edit_mode):

    # header
    container = layout.box()

    container.prop(settings, "tools_expanded", icon=get_expander_icon(settings.tools_expanded), emboss=False, text="Tools")
    if not settings.tools_expanded:
        return

    container = container.box()

    # interactive uv tool
    col = container.column()
    col.enabled = in_edit_mode

    text = "Edit UVs" if in_edit_mode else "Edit UVs (edit mode)"
    col.operator("view3d.nuv_interactiveuveditor", text=text)
    c_row = col.row()
    c_row.split(factor=0.3)

    c_row.label(text="Edit Uvs Settings")

    c_col = c_row.column()
    c_col.prop(settings, "uv_editor_linked_faces")
    c_col.prop(settings, "uv_edit_pixel_snap")

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


def ui_draw_rects(layout, context, settings, in_edit_mode):

    # header
    container = layout.box()

    container.prop(settings, "rects_expanded", icon=get_expander_icon(settings.rects_expanded), emboss=False, text="Rect Sets")
    if not settings.rects_expanded:
        return

    container = container.box()
    max_items_per_row = round(context.region.width / (32 * nuv_preview_scale))

    collection_list = bpy.context.scene.nuv_uvSets
    collection_len = len(collection_list)

    if collection_len == 0:
        container.label(text="You haven't imported any sets yet.")
        return

    for i in range(0, collection_len):
        expanded = ui_draw_collection(collection_list[i], i, max_items_per_row, container, context, in_edit_mode)
        if expanded: container.separator(factor=1)


def ui_draw_collection(collection, idx, max_items_per_row, layout, context, in_edit_mode):

    # title
    row = layout.row()
    split = row.split(factor=0.9, align=True)

    split.prop(collection, "expanded", icon=get_expander_icon(collection.expanded), emboss=True, text=collection.name)
    split.alert = True

    op = split.operator("neo.uvset_delete", icon="TRASH", text="")
    op.collectionIdx = idx

    if not collection.expanded:
        return False

    # rect actions
    layout = layout.box()

    if collection.relative_path:
        row = layout.row()
        split = row.split(factor=0.9)
        split.label(text=collection.relative_path)

        op = split.operator("neo.uv_uireload", text="", icon="FILE_REFRESH")
        op.collectionIdx = idx

    row = layout.row()
    op = row.operator("view3d.nuv_set_uv_rect_selector", text="Select UV", icon="UV_FACESEL", emboss=True)
    op.collectionIdx = idx

    row = row.row()
    row.enabled = in_edit_mode

    text = "Paint UV" if in_edit_mode else "Paint UV (edit mode)"
    op = row.operator("view3d.nuv_set_paint_rect_selector", text=text, emboss=True, icon="BRUSHES_ALL")
    op.collectionIdx = idx

    ui_draw_collection_patterns(collection, idx, layout, in_edit_mode)
    ui_draw_collection_rect_list(collection, idx, max_items_per_row, layout, in_edit_mode)

    return True


def ui_draw_collection_patterns(collection, idx, layout, in_edit_mode):
    layout.prop(collection, "patterns_expanded", icon=get_expander_icon(collection.patterns_expanded), emboss=True, text="Patterns")

    if not collection.patterns_expanded:
        return

    patterns_len = len(collection.patterns.items())

    row = layout.row()

    split = row.split(factor=0.9)
    col = split.column()
    col.template_list("NeoPatternList", "", collection, "patterns", collection, "active_pattern")

    col = split.column()
    op = col.operator("neo.uvset_add_pattern", text="", icon="ADD")
    op.collectionIdx = idx

    col = col.column()
    col.enabled = patterns_len > 0
    op = col.operator("neo.uvset_delete_pattern", text="", icon="REMOVE")
    op.collectionIdx = idx

    active_pattern = collection.get_active_pattern()

    if active_pattern is None:
        return

    paint = layout

    row = paint.row()
    row.enabled = in_edit_mode
    text = "Paint" if in_edit_mode else "Paint (edit mode)"
    op = row.operator("view3d.nuv_pattern_paint", text=text)
    op.collectionIdx = idx

    text = "Random" if in_edit_mode else "Random (edit mode)"
    op = row.operator("neo.uv_patternunwrap", text=text)
    op.collectionIdx = idx

    row = paint.row()
    row.alignment = "LEFT"
    row.prop(active_pattern, "use_random", text="Use Random")

    row = row.row()
    row.alignment = "LEFT"
    row.enabled = not active_pattern.use_random
    row.prop(active_pattern, "reset_stroke_on_click", text="Reset Strokes")

    row = paint.row()
    row.alignment = "LEFT"
    row.prop(active_pattern, "allow_repaint", text="Allow Repaint")

    pattern_box = layout.box()

    op = pattern_box.operator("neo.uvset_add_pattern_rect", text="", icon="ADD")
    op.collectionIdx = idx

    pattern_layout = pattern_box.column()
    pattern_idx = -1

    pattern_len = len(active_pattern.items.items())
    for pattern_rect in active_pattern.items:
        pattern_idx += 1

        rect = pattern_rect.get_rect(collection)

        if rect is None:
            preview_image = None
        else:
            preview_image = get_image_by_name(rect.previewName)

        if preview_image is not None and bpy.app.version[0] >= 3:
            preview_image.preview_ensure()

        row = pattern_layout.row()
        row.alignment = "CENTER"
        split = row.split(factor=0.85)

        col = split.column()

        if preview_image is None: col.template_icon(icon_value=rect_missing_icon, scale=nuv_pattern_preview_scale)
        else: col.template_icon(icon_value=preview_image.preview.icon_id, scale=nuv_pattern_preview_scale)

        col = split.column()
        col.separator(factor=0.25)
        op = col.operator("neo.uvset_delete_pattern_rect", text="", icon="TRASH")
        op.collectionIdx = idx
        op.patternRectIdx = pattern_idx

        op = col.operator("view3d.nuv_set_pattern_rect_selector", text="", icon="RESTRICT_SELECT_OFF")
        op.collectionIdx = idx
        op.patternRectIdx = pattern_idx

        col.separator(factor=1)
        up_col = col.column()
        up_col.enabled = pattern_idx > 0
        op = up_col.operator("neo.uvset_move_pattern_rect", text="", icon="TRIA_UP")
        op.collectionIdx = idx
        op.patternRectIdx = pattern_idx
        op.up = True

        down_col = col.column()
        down_col.enabled = pattern_idx < pattern_len - 1
        op = down_col.operator("neo.uvset_move_pattern_rect", text="", icon="TRIA_DOWN")
        op.collectionIdx = idx
        op.patternRectIdx = pattern_idx
        op.up = False


def ui_draw_collection_rect_list(collection, idx, max_items_per_row, layout, in_edit_mode):
    layout.prop(collection, "items_expanded", icon=get_expander_icon(collection.items_expanded), emboss=True, text="Rect List")

    if not collection.items_expanded:
        return

    items = collection.items
    item_len = len(items)

    layout = layout.box()
    row = layout.row()
    row.label(text="Page")
    op = row.operator("neo.uv_uiprevpage")
    op.collectionIdx = idx

    op = row.operator("neo.uv_uinextpage")
    op.collectionIdx = idx

    op = row.operator("neo.uv_uifirstpage")
    op.collectionIdx = idx

    # calculate page range
    start = collection.page * nuv_max_item_per_page
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
        op.collectionIdx = idx
        op.rectIdx = j

        row_i += 1


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
    NeoSidebarPanel,
    NeoUvUiSettings,
    NeoPatternList,
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