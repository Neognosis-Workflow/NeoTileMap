# region Imports
import bpy
import gpu
from . import nImageOp
from . import nUtil
from . import nData
from . import nMath
import mathutils

is_blender_4_or_greater = bpy.app.version[0] > 3

# blender 4.4 must have additional params for __init__
is_blender_44_or_greater = is_blender_4_or_greater and bpy.app.version[1] > 3

# endregion

# region Operators


# noinspection PyAttributeOutsideInit
class NeoRectSelector(nImageOp.NeoImageOperator):
    bl_idname = "view3d.nuv_rect_selector"
    bl_label = "Rect Selector"

    collectionIdx: bpy.props.IntProperty()
    openHighlightIdx: bpy.props.IntProperty(default=-1)

    if is_blender_44_or_greater:
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.init()
    else:
        def __init__(self):
            super().__init__()
            self.init()

    def init(self):
        super().init()
        self.dragging = False
        self.finished = False
        self.highlighted_Item = None

    def on_open(self, context, event):
        self.collection = bpy.context.scene.nuv_uvSets[self.collectionIdx]

        img_name = f"Atlas_{self.collection.name}"

        if is_blender_4_or_greater:
            image = gpu.texture.from_image(bpy.data.images[img_name])
        else:
            image = bpy.data.images[img_name]

        args = (self, image, self.collection.items, context)
        self.handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_tool, args, 'WINDOW', 'POST_PIXEL')
        self.zoom = 0.85  # NEW: Make sure the image is framed nicely

        bpy.context.scene.nuv_settings.last_uv_set = self.collectionIdx

        try:
            if self.openHighlightIdx > 0:
                self.snap_mouse_to_open_highlight(context, image, self.openHighlightIdx)
        except Exception as e:
            print(e)

    def on_update(self, context, event):
        if self.dragging:
            self.offset_x += self.mouse_delta_x
            self.offset_y += self.mouse_delta_y

        return self.finished

    def on_rect_selected(self, collection_idx, rect_idx):
        pass

    def on_mouse_down(self, context, btn_idx):
        if btn_idx == 0:
            if self.highlighted_Item is None:
                return
            else:
                self.finished = True

                idx = -1
                for item in self.collection.items:
                    idx += 1
                    if self.highlighted_Item.__eq__(item):
                        break

                try:
                    self.on_rect_selected(self.collectionIdx, idx)
                except Exception as e:
                    print(e)

        if btn_idx == 2:
            self.dragging = True

        if btn_idx == 1:
            self.finished = True

    def on_mouse_up(self, context, btn_idx):
        if btn_idx == 2:
            self.dragging = False

    def on_scroll_down(self, context):
        zoom_amt = 0.1 * self.zoom

        self.zoom -= zoom_amt
        if self.zoom < 0.001: self.zoom = 0.001

        self.update_zoom(self.zoom + zoom_amt, True)

    def on_scroll_up(self, context):
        zoom_amt = 0.1 * self.zoom

        self.zoom += zoom_amt
        self.update_zoom(self.zoom - zoom_amt, False)

    def update_zoom(self, old_zoom, zoom_out):
        if zoom_out:
            self.offset_x = self.offset_x + (1.0 - (self.zoom / old_zoom)) * -self.offset_x
            self.offset_y = self.offset_y + (1.0 - (self.zoom / old_zoom)) * -self.offset_y
        else:
            self.offset_x = self.offset_x + (1.0 - (self.zoom / old_zoom)) * -self.offset_x
            self.offset_y = self.offset_y + (1.0 - (self.zoom / old_zoom)) * -self.offset_y

    def on_close(self, context, event):
        bpy.context.window.cursor_modal_restore()
        bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')

    def snap_mouse_to_open_highlight(self, context, atlas, rect_idx):
        self.img_data = nUtil.get_transformed_image_data(atlas, context.area.width, context.area.height,
                                                         self.zoom, self.offset_x, self.offset_y)

        rect = self.collection.items.items()[rect_idx][1]

        center = self.get_center()
        size = self.get_size()

        top_left = center + mathutils.Vector(nData.rect_top_left(rect)) * size
        top_right = center + mathutils.Vector(nData.rect_top_right(rect)) * size
        bottom_right = center + mathutils.Vector(nData.rect_bottom_right(rect)) * size
        bottom_left = center + mathutils.Vector(nData.rect_bottom_left(rect)) * size

        mouse_center = (top_left + top_right + bottom_left + bottom_right) / 4

        region_x = context.area.x + mouse_center.x
        region_y = context.area.y + mouse_center.y
        context.window.cursor_warp(int(region_x), int(region_y))

    def get_center(self):
        return mathutils.Vector((self.img_data[3], self.img_data[4])) + mathutils.Vector((self.offset_x, self.offset_y))

    def get_size(self):
        return mathutils.Vector((self.img_data[1], self.img_data[2])) * 0.5

    @staticmethod
    def draw_tool(self, atlas, items, context):
        self.img_data = nUtil.get_transformed_image_data(atlas, context.area.width, context.area.height,
                                                         self.zoom, self.offset_x, self.offset_y)

        nUtil.draw_transformed_image(atlas, self.img_data[5], self.img_data[6], self.img_data[7], self.img_data[8])

        center = self.get_center()
        size = self.get_size()

        lineColor = (0.0, 0.0, 1.0, 1.0)
        highlightColor = (0.0, 1.0, 0.0, 1.0)

        if self.dragging is True:
            # mouse wrapping
            if self.mouse_x > context.area.x + context.area.width:
                context.window.cursor_warp(context.area.x, self.mouse_y)

            if self.mouse_x < context.area.x:
                context.window.cursor_warp(context.area.x + context.area.width, self.mouse_y)

            if self.mouse_y > context.area.y + context.area.height:
                context.window.cursor_warp(self.mouse_x, context.area.y)

            if self.mouse_y < context.area.y:
                context.window.cursor_warp(self.mouse_x, context.area.y + context.area.height)

            bpy.context.window.cursor_modal_set("SCROLL_XY")
        else:
            bpy.context.window.cursor_modal_set("DEFAULT")

        if hasattr(self, "collection"):
            self.highlighted_Item = None

            has_highlight = False
            highlight_top_left = None
            highlight_top_right = None
            highlight_bottom_Right = None
            highlight_bottom_left = None

            # draw items
            for item in self.collection.items:
                top_left = center + mathutils.Vector(nData.rect_top_left(item)) * size
                top_right = center + mathutils.Vector(nData.rect_top_right(item)) * size
                bottom_right = center + mathutils.Vector(nData.rect_bottom_right(item)) * size
                bottom_left = center + mathutils.Vector(nData.rect_bottom_left(item)) * size

                mouse_in_bounds = nUtil.mouse_in_bounds(self.mouse_region_x, self.mouse_region_y, top_left, top_right, bottom_right, bottom_left)
                if mouse_in_bounds and not has_highlight and not self.dragging:
                    self.highlighted_Item = item

                    has_highlight = True
                    highlight_top_left = top_left
                    highlight_top_right = top_right
                    highlight_bottom_Right = bottom_right
                    highlight_bottom_left = bottom_left
                else:
                    nUtil.line_draw(top_left, top_right, lineColor)
                    nUtil.line_draw(top_right, bottom_right, lineColor)
                    nUtil.line_draw(bottom_right, bottom_left, lineColor)
                    nUtil.line_draw(bottom_left, top_left, lineColor)

            # draw highlighted item
            if has_highlight and not self.dragging:
                nUtil.line_draw(highlight_top_left, highlight_top_right, highlightColor)
                nUtil.line_draw(highlight_top_right, highlight_bottom_Right, highlightColor)
                nUtil.line_draw(highlight_bottom_Right, highlight_bottom_left, highlightColor)
                nUtil.line_draw(highlight_bottom_left, highlight_top_left, highlightColor)
        else:
            self.highlighted_Item = None


class NeoSetUvRectSelector(NeoRectSelector):
    bl_idname = "view3d.nuv_set_uv_rect_selector"
    bl_label = "Set UV Rect Selector"
    bl_description = "Select a rect and unwrap it onto the selected faces."

    def on_rect_selected(self, collection_idx, rect_idx):
        bpy.ops.neo.uv_setuvrect('INVOKE_DEFAULT', collectionIdx=collection_idx, rectIdx=rect_idx)


class NeoSetPaintRectSelector(NeoRectSelector):
    bl_idname = "view3d.nuv_set_paint_rect_selector"
    bl_label = "Paint Rect Selector."
    bl_description = "Paint UVs. Right click to select a different rect.\nHold CTRL while painting to flip horizontally and CTRL + Shift to flip vertically.\nHold ALT and use the scrollwheel to rotate UVs.\nHold ALT and left click a face to pick its rect and make it the active one.\nHold ALT, Shift and CTRL to access the properties panel settings."

    def on_rect_selected(self, collection_idx, rect_idx):
        bpy.ops.neo.uv_paintunwrap(
            "INVOKE_DEFAULT",
            collectionIdx=collection_idx,
            rectIdx=rect_idx)


class NeoSetPatternRectSelector(NeoRectSelector):
    bl_idname = "view3d.nuv_set_pattern_rect_selector"
    bl_label = "Set Pattern Rect Selector"

    patternRectIdx: bpy.props.IntProperty()

    def on_rect_selected(self, collection_idx, rect_idx):
        bpy.ops.neo.uvset_set_pattern_rect(
            "INVOKE_DEFAULT",
            collectionIdx=collection_idx,
            rectIdx=rect_idx,
            patternRectIdx=self.patternRectIdx)

# endregion

# region Blender


classes = (
    NeoSetUvRectSelector,
    NeoSetPaintRectSelector,
    NeoSetPatternRectSelector,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

# endregion
