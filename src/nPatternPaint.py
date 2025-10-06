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
class NeoPatternPaint(bpy.types.Operator):
    bl_idname = "view3d.nuv_pattern_paint"
    bl_label = "Pattern Painter"
    bl_description = "Paint the pattern onto faces."
    bl_options = {"REGISTER", "UNDO"}

    collectionIdx: bpy.props.IntProperty()

    @staticmethod
    def draw_callback_v(self, context):
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
        self.tree = BVHTree.FromBMesh(self.edit_mesh, epsilon=0.1)
        self.hit_face = None
        self.last_hit_face = None
        self.hit_component = None
        self.left_mouse_held = False
        self.waiting_to_assign_reset_idx = False
        self.painted_faces = []

        self.collection = nData.get_collection_by_idx(self.collectionIdx)
        self.pattern = self.collection.get_active_pattern()
        self.items = self.pattern.items.items()
        self.pattern_len = len(self.items)

        self.paint_idx = 0

        # setup handlers
        self.handle_v = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_v, (self, context), "WINDOW",
                                                               "POST_VIEW")
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def draw_filled_face(self, face, world_matrix):
        if not self.edit_mesh.is_valid: return
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

        self.hit_face = self.edit_mesh.faces[self.hit_result[2]]

    def stroke_step(self, context, face, event):
        # unwrap variables
        space_mode = bpy.context.scene.nuv_settings.mode_space
        unwrap_mode = bpy.context.scene.nuv_settings.mode_unwrap
        correct_aspect = bpy.context.scene.nuv_settings.correct_aspect_ratio
        snap_to_bounds = bpy.context.scene.nuv_settings.snap_to_bounds

        # get active uv layer
        layer = self.edit_mesh.loops.layers.uv
        uv_layer = layer.verify()

        # idx update
        if self.pattern.use_random: self.paint_idx = random.randrange(0, self.pattern_len)
        elif self.paint_idx > self.pattern_len - 1: self.paint_idx = 0

        # update uv
        pattern_rect = self.items[self.paint_idx][1]
        rect = pattern_rect.get_rect(self.collection)

        nUv.unwrap_auto(space_mode, False, context, self.obj.matrix_world, {face},
                        unwrap_mode, correct_aspect, snap_to_bounds, rect, uv_layer)

        # increment and update
        self.paint_idx += 1
        bmesh.update_edit_mesh(self.mesh, loop_triangles=False, destructive=False)

    def modal(self, context, event):
        if bpy.context.active_object.mode != "EDIT":
            self.finished()
            return {"FINISHED"}

        context.area.tag_redraw()

        # try finish
        if nUtil.should_modal_escape(event) or event.type == "RIGHTMOUSE":
            self.finished()
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
                collection = nData.get_collection_by_idx(self.collectionIdx)
                pattern = collection.get_active_pattern()
                self.waiting_to_assign_reset_idx = pattern.reset_stroke_on_click
                if event.shift: self.waiting_to_assign_reset_idx = not self.waiting_to_assign_reset_idx

            if event.value == "RELEASE": self.left_mouse_held = False

        # mouse interact
        if self.hit_face is not self.last_hit_face:
            self.last_hit_face = self.hit_face

            if self.hit_face is not None and self.left_mouse_held:
                if self.waiting_to_assign_reset_idx:
                    self.paint_idx = 0
                    self.waiting_to_assign_reset_idx = False

                if self.pattern.allow_repaint or (self.hit_face not in self.painted_faces):
                    self.stroke_step(context, self.hit_face, event)

                if self.hit_face not in self.painted_faces:
                    self.painted_faces.append(self.hit_face)


        if self.left_mouse_held or event.type == "LEFTMOUSE":
            return {"RUNNING_MODAL"}
        else:
            return {"PASS_THROUGH"}

    def finished(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.handle_v, "WINDOW")

# endregion

# region Blender


classes = (
    NeoPatternPaint,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

# endregion