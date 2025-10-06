# region Imports

import sys

import bpy
import bmesh
import math
import random
from . import nData
from . import nMath
from . import nUtil
from . import nUv
from . import nInterface

from mathutils import Vector
from mathutils.bvhtree import BVHTree

from bpy_extras import view3d_utils

import gpu
import gpu_extras
from gpu_extras.presets import draw_circle_2d
from gpu_extras.batch import batch_for_shader

is_blender_4_or_greater = bpy.app.version[0] > 3

# blender 4.4 must have additional params for __init__
is_blender_44_or_greater = is_blender_4_or_greater and bpy.app.version[1] > 3

# endregion

# region Operators


# noinspection PyAttributeOutsideInit
class NeoPaint(bpy.types.Operator):
    bl_idname = "view3d.nuv_paint"
    bl_label = "Rect Painter"
    bl_description = "Paint the selected rect onto faces."
    bl_options = {"REGISTER", "UNDO"}

    collectionIdx: bpy.props.IntProperty()
    rectIdx: bpy.props.IntProperty()

    @staticmethod
    def draw_callback_v(self, context):
        if not self.edit_mesh.is_valid: return
        component = self.hit_face
        if component is not None:
            world_matrix = self.obj.matrix_world

            if isinstance(component, bmesh.types.BMFace):
                self.draw_filled_face(component, world_matrix)

    if is_blender_44_or_greater:
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.init()
    else:
        def __init__(self):
            super().__init__()
            self.init()

    def init(self):
        # setup drawing data
        if is_blender_4_or_greater:
            self.line_shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            self.circle_shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        else:
            self.line_shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
            self.circle_shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")

        self.hit_result = None

    def invoke(self, context, event):
        # make sure we're in edit mode
        t = bpy.context.object.type
        if t != "MESH": return {"FINISHED"}
        if bpy.context.active_object.mode != "EDIT": return {"FINISHED"}

        # init variables
        self.obj = bpy.context.object
        self.mesh = self.obj.data
        self.edit_mesh = bmesh.from_edit_mesh(self.mesh)
        self.tree = BVHTree.FromBMesh(self.edit_mesh, epsilon=nUtil.raycast_epsilon)
        self.hit_face = None
        self.last_hit_face = None
        self.hit_component = None
        self.left_mouse_held = False

        self.collection = nData.get_collection_by_idx(self.collectionIdx)
        self.rect = self.collection.get_rect(self.rectIdx)

        # setup handlers
        self.handle_v = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_v, (self, context), "WINDOW",
                                                               "POST_VIEW")
        context.window_manager.modal_handler_add(self)

        bpy.context.scene.nuv_settings.last_uv_set = self.collectionIdx

        return {'RUNNING_MODAL'}

    def draw_filled_face(self, face, world_matrix):
        # wire
        self.line_shader.uniform_float("color", (1, 1, 0, 1))

        line_coords = []
        for e in face.edges:
            line_coords.append((world_matrix @ e.verts[0].co).to_tuple())
            line_coords.append((world_matrix @ e.verts[1].co).to_tuple())

        line_batch = batch_for_shader(self.line_shader, "LINES", {"pos": line_coords})
        line_batch.draw(self.line_shader)

    def try_assign_face(self):
        self.hit_face = None
        if self.hit_result is None: return
        if self.edit_mesh is None: return
        if not self.edit_mesh.is_valid: return

        self.hit_face = self.edit_mesh.faces[self.hit_result[2]]

    def unwrap(self, context, face, event):
        # unwrap variables
        space_mode = bpy.context.scene.nuv_settings.mode_space
        unwrap_mode = bpy.context.scene.nuv_settings.mode_unwrap
        correct_aspect = bpy.context.scene.nuv_settings.correct_aspect_ratio
        snap_to_bounds = bpy.context.scene.nuv_settings.snap_to_bounds

        # get active uv layer
        layer = self.edit_mesh.loops.layers.uv
        uv_layer = layer.verify()

        # update uv
        face = {face}
        nUv.unwrap_auto(space_mode, False, context, self.obj.matrix_world, face,
                        unwrap_mode, correct_aspect, snap_to_bounds, self.rect, uv_layer)

        if event.ctrl:
            nUv.flip(False, face, not event.shift, uv_layer)

        # increment and update
        bmesh.update_edit_mesh(self.mesh, loop_triangles=False, destructive=False)

    def rotate(self, context, face, clockwise):
        layer = self.edit_mesh.loops.layers.uv
        uv_layer = layer.verify()

        nUv.rotate(False, {face}, clockwise, uv_layer)

        # increment and update
        bmesh.update_edit_mesh(self.mesh, loop_triangles=False, destructive=False)

    def try_set_rect_from_face(self, context, face):
        layer = self.edit_mesh.loops.layers.uv
        uv_layer = layer.verify()

        new_rect = nUv.get_best_rect_for_face(face, uv_layer, self.collection)
        if new_rect is not None:
            self.report({"INFO"}, "Picked rect from face.")
            self.rect = new_rect
        else:
            self.report({"ERROR"}, "Couldn't find a relevant rect to pick from the face.")

    def modal(self, context, event):
        if bpy.context.active_object.mode != "EDIT":
            self.finished()
            return {"FINISHED"}

        context.area.tag_redraw()

        all_modifiers = event.shift and event.ctrl and event.alt
        if all_modifiers:
            nInterface.only_draw_settings_this_frame()

            if nInterface.is_mouse_in_neognosis_sidebar(event):
                return {"PASS_THROUGH"}

        # try finish
        right_mouse = event.type == "RIGHTMOUSE"
        if nUtil.should_modal_escape(event) or right_mouse:
            self.finished()

            if right_mouse:
                bpy.ops.view3d.nuv_set_paint_rect_selector("INVOKE_DEFAULT", collectionIdx=self.collectionIdx,
                                                           openHighlightIdx=self.rectIdx)
            return {"FINISHED"}

        # update face
        hit_results = nUtil.raycast_mesh_from_screen(self.obj, self.tree, event)
        if hit_results is not None:
            self.hit_result = hit_results[0]
        else:
            self.hit_result = None
        self.try_assign_face()

        # inputs
        if event.type == "LEFTMOUSE":
            if event.value == "PRESS":
                self.last_hit_face = None
                self.left_mouse_held = True

            if event.value == "RELEASE": self.left_mouse_held = False

        # mouse interact
        if event.alt and self.hit_face:
            if event.type == "WHEELUPMOUSE":
                self.rotate(context, self.hit_face, True)
                return {"RUNNING_MODAL"}
            if event.type == "WHEELDOWNMOUSE":
                self.rotate(context, self.hit_face, False)
                return {"RUNNING_MODAL"}

        if self.hit_face is not self.last_hit_face:
            self.last_hit_face = self.hit_face

            if self.hit_face is not None and self.left_mouse_held:
                if event.alt:
                    self.try_set_rect_from_face(context, self.hit_face)
                else:
                    self.unwrap(context, self.hit_face, event)

        if self.left_mouse_held or event.type == "LEFTMOUSE":
            return {"RUNNING_MODAL"}
        else:
            return {"PASS_THROUGH"}

    def finished(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.handle_v, "WINDOW")

# endregion

# region Blender


classes = (
    NeoPaint,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

# endregion
