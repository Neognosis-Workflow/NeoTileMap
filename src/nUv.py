# region Imports

import bpy
import os
import bmesh
import mathutils
import random
from . import nMath
from . import nInterface
from . import nUtil
from . import nData

# endregion

# region Global Methods


def paint_post_unwrap(event, face, uv_layer):
    if event.alt:
        if event.shift:
            rotate(False, face, False, uv_layer)
        elif event.ctrl:
            rotate(False, face, True, uv_layer)
            rotate(False, face, True, uv_layer)
        else:
            rotate(False, face, True, uv_layer)

    elif event.ctrl:
        flip(False, face, not event.shift, uv_layer)


def get_best_rect_for_face(face, uv_layer, collection):

    # calculate center
    uv_center = mathutils.Vector((0.0, 0.0))

    itr = 0
    for vert, loop in zip(face.verts, face.loops):
        uv = loop[uv_layer].uv
        uv_center += uv
        itr += 1

    uv_center /= itr

    # check rect bounds
    idx = -1
    for rect in collection.items:
        idx += 1
        if nData.rect_contains(rect, uv_center.x, uv_center.y):
            return rect, idx

    return None


def rotate(only_selected, faces, clockwise, uv_layer):
    rotate_mode = bpy.context.scene.nuv_settings.mode_rotate
    use_bounds = bpy.context.scene.nuv_settings.transform_uses_bounds
    space_mode = bpy.context.scene.nuv_settings.mode_space

    if space_mode == "perface":
        for face in faces:
            if not face.select and only_selected: continue

            if rotate_mode == "shift":

                # build uv list
                uv_list = []
                for vert, loop in zip(face.verts, face.loops):
                    uv = loop[uv_layer].uv
                    uv_list.append(mathutils.Vector((uv.x, uv.y)))

                # shift uvs around
                vert_len = len(face.verts)
                idx = 0

                for vert, loop in zip(face.verts, face.loops):
                    if clockwise:
                        new_idx = idx + 1
                        if new_idx > vert_len - 1: new_idx = 0
                    else:
                        new_idx = idx - 1
                        if new_idx < 0: new_idx = vert_len - 1

                    loop[uv_layer].uv = uv_list[new_idx]
                    idx += 1
            else:
                # calculate uv center
                uv_center = mathutils.Vector((0.0, 0.0))

                if use_bounds:
                    bounds_init = 1000000000
                    uv_bounds_min = mathutils.Vector((bounds_init, bounds_init))
                    uv_bounds_max = mathutils.Vector((-bounds_init, -bounds_init))

                    for loop in face.loops:
                        uv = loop[uv_layer].uv

                        if uv.x < uv_bounds_min.x: uv_bounds_min.x = uv.x
                        if uv.y < uv_bounds_min.y: uv_bounds_min.y = uv.y

                        if uv.x > uv_bounds_max.x: uv_bounds_max.x = uv.x
                        if uv.y > uv_bounds_max.y: uv_bounds_max.y = uv.y

                    uv_center = (uv_bounds_min + uv_bounds_max) / 2.0
                else:
                    vert_len = len(face.verts)
                    if vert_len == 3:
                        uv_center = nMath.center_for_triangle(face.loops[0][uv_layer].uv, face.loops[1][uv_layer].uv,
                                                              face.loops[2][uv_layer].uv)
                    else:
                        itr = 0
                        for loop in face.loops:
                            uv = loop[uv_layer].uv
                            uv_center += uv
                            itr += 1

                        uv_center /= itr

                for loop in face.loops:
                    uv = loop[uv_layer].uv

                    uv = nMath.rotate_vector(uv, uv_center, 90 if clockwise else -90)
    else:
        bounds_init = 1000000000
        uv_bounds_min = mathutils.Vector((bounds_init, bounds_init))
        uv_bounds_max = mathutils.Vector((-bounds_init, -bounds_init))

        # calculate bounds for all uvs
        selected_faces = []
        for face in faces:
            if not face.select and only_selected: continue

            selected_faces.append(face)

            for loop in face.loops:
                uv = loop[uv_layer].uv

                if uv.x < uv_bounds_min.x: uv_bounds_min.x = uv.x
                if uv.y < uv_bounds_min.y: uv_bounds_min.y = uv.y

                if uv.x > uv_bounds_max.x: uv_bounds_max.x = uv.x
                if uv.y > uv_bounds_max.y: uv_bounds_max.y = uv.y

        uv_center = (uv_bounds_min + uv_bounds_max) / 2.0

        for face in selected_faces:
            for loop in face.loops:
                uv = loop[uv_layer].uv

                uv = nMath.rotate_vector(uv, uv_center, 90 if clockwise else -90)


def flip(only_selected, faces, horizontal, uv_layer):
    use_bounds = bpy.context.scene.nuv_settings.transform_uses_bounds
    space_mode = bpy.context.scene.nuv_settings.mode_space

    if space_mode == "perface":
        for face in faces:
            if not face.select and only_selected: continue

            # calculate uv center
            uv_center = mathutils.Vector((0.0, 0.0))

            if use_bounds:
                bounds_init = 1000000000
                uv_bounds_min = mathutils.Vector((bounds_init, bounds_init))
                uv_bounds_max = mathutils.Vector((-bounds_init, -bounds_init))

                for loop in face.loops:
                    uv = loop[uv_layer].uv

                    if uv.x < uv_bounds_min.x: uv_bounds_min.x = uv.x
                    if uv.y < uv_bounds_min.y: uv_bounds_min.y = uv.y

                    if uv.x > uv_bounds_max.x: uv_bounds_max.x = uv.x
                    if uv.y > uv_bounds_max.y: uv_bounds_max.y = uv.y

                uv_center = (uv_bounds_min + uv_bounds_max) / 2.0
            else:
                vert_len = len(face.verts)
                if vert_len == 3:
                    uv_center = nMath.center_for_triangle(face.loops[0][uv_layer].uv, face.loops[1][uv_layer].uv,
                                                          face.loops[2][uv_layer].uv)
                else:
                    itr = 0
                    for loop in face.loops:
                        uv = loop[uv_layer].uv
                        uv_center += uv
                        itr += 1

                    uv_center /= itr

            # perform the flip
            for loop in face.loops:
                uv = loop[uv_layer].uv

                if horizontal:
                    offset_x = uv.x - uv_center.x
                    uv.x = uv_center.x + -offset_x
                else:
                    offset_y = uv.y - uv_center.y
                    uv.y = uv_center.y + -offset_y
    else:
        bounds_init = 1000000000
        uv_bounds_min = mathutils.Vector((bounds_init, bounds_init))
        uv_bounds_max = mathutils.Vector((-bounds_init, -bounds_init))

        # calculate bounds for all uvs
        selected_faces = []
        for face in faces:
            if not face.select and only_selected: continue

            selected_faces.append(face)

            for loop in face.loops:
                uv = loop[uv_layer].uv

                if uv.x < uv_bounds_min.x: uv_bounds_min.x = uv.x
                if uv.y < uv_bounds_min.y: uv_bounds_min.y = uv.y

                if uv.x > uv_bounds_max.x: uv_bounds_max.x = uv.x
                if uv.y > uv_bounds_max.y: uv_bounds_max.y = uv.y

        uv_center = (uv_bounds_min + uv_bounds_max) / 2.0

        for face in selected_faces:
            # perform the flip
            for loop in face.loops:
                uv = loop[uv_layer].uv

                if horizontal:
                    offset_x = uv.x - uv_center.x
                    uv.x = uv_center.x + -offset_x
                else:
                    offset_y = uv.y - uv_center.y
                    uv.y = uv_center.y + -offset_y


def unwrap_auto(space_mode, only_selected, context, mw, faces, unwrap_mode, correct_aspect, snap_mode, rect,
                uv_layer):
    """Unwraps selected faces, automatically choosen between local of world unwrap based on the value of space_mode"""
    if space_mode == "perface":
        unwrap_local(only_selected, context, mw, faces, unwrap_mode, correct_aspect, snap_mode, rect, uv_layer)
    else:
        unwrap_global(only_selected, context, mw, faces, unwrap_mode, correct_aspect, snap_mode, rect, uv_layer)


def unwrap_local(only_selected, context, mw, faces, unwrap_mode, correct_aspect, snap_mode, rect, uv_layer):
    """
    Unwraps selected faces local to themselves.
    """

    normalize_to_bounds = snap_mode == "to_bounds"

    # enumerate selected faces
    for face in faces:
        if not face.select and only_selected: continue

        # get face data
        center = mw @ mathutils.Vector(face.calc_center_median())
        normal = mw.inverted().transposed().to_3x3() @ mathutils.Vector(face.normal)
        tangent = mw.to_quaternion() @ face.calc_tangent_edge_pair()

        # calculate face rotation
        unwrap_axis = bpy.context.scene.nuv_settings.unwrap_axis
        if unwrap_mode == "face":
            unwrap_up = tangent
        elif unwrap_mode == "world":
            unwrap_up = mathutils.Vector(unwrap_axis)
        elif unwrap_mode == "object":
            unwrap_up = mw.to_quaternion() @ mathutils.Vector(unwrap_axis)
        elif unwrap_mode == "camera":
            unwrap_up = context.space_data.region_3d.view_rotation @ mathutils.Vector(unwrap_axis)
        else:
            unwrap_up = tangent

        face_dir = (center + normal - center).normalized()
        face_rot = nMath.axis_to_quat(face_dir, unwrap_up)

        face_rot_axis_angle = face_rot.to_axis_angle()
        face_matrix_loc = mathutils.Matrix.Translation((center.x, center.y, center.z))
        face_matrix_rot = mathutils.Matrix.Rotation(face_rot_axis_angle[1], 4, face_rot_axis_angle[0])
        face_matrix = face_matrix_loc @ face_matrix_rot

        # enumerate verts
        max_dim_x = 0
        max_dim_y = 0
        verts_local_face = []

        for vert in face.verts:
            vert_world = mw @ vert.co
            vert_local_face = face_matrix.inverted() @ vert_world

            verts_local_face.append(vert_local_face)

            if abs(vert_local_face.x) > max_dim_x: max_dim_x = abs(vert_local_face.x)
            if abs(vert_local_face.y) > max_dim_y: max_dim_y = abs(vert_local_face.y)

        # correct triangle dim
        vert_len = len(verts_local_face)
        if vert_len == 3:
            max_dim_x /= 2
            max_dim_y /= 2

        if correct_aspect:
            aspect = max_dim_x / max_dim_y

            if aspect >= 1: max_dim_y = max_dim_x
            else: max_dim_x = max_dim_y

        # unwrap
        if normalize_to_bounds:
            bounds_init = 1000000000
            uv_bounds_min = mathutils.Vector((bounds_init, bounds_init))
            uv_bounds_max = mathutils.Vector((-bounds_init, -bounds_init))

        itr = 0
        for loop in face.loops:
            if unwrap_mode == "none" and vert_len <= 4:
                if itr == 0:
                    x = (rect.topLeftX + 1.0) / 2.0
                    y = (rect.topLeftY + 1.0) / 2.0
                    uv = mathutils.Vector((x, y))
                elif itr == 1:
                    x = (rect.topRightX + 1.0) / 2.0
                    y = (rect.topRightY + 1.0) / 2.0
                    uv = mathutils.Vector((x, y))
                elif itr == 2:
                    x = (rect.bottomRightX + 1.0) / 2.0
                    y = (rect.bottomRightY + 1.0) / 2.0
                    uv = mathutils.Vector((x, y))
                elif itr == 3:
                    x = (rect.bottomLeftX + 1.0) / 2.0
                    y = (rect.bottomLeftY + 1.0) / 2.0
                    uv = mathutils.Vector((x, y))

                loop[uv_layer].uv = uv
            else:
                # normalized to total uv space
                x = ((verts_local_face[itr].x / max_dim_x) + 1.0) / 2.0
                y = ((verts_local_face[itr].y / max_dim_y) + 1.0) / 2.0

                # scale down to rect
                top_left = nData.rect_top_left(rect)
                top_right = nData.rect_top_right(rect)
                bottom_left = nData.rect_bottom_left(rect)
                bottom_right = nData.rect_bottom_right(rect)

                x = nMath.lerp((top_left[0] + 1.0) / 2.0, (top_right[0] + 1.0) / 2.0, x, True)
                y = nMath.lerp((bottom_left[1] + 1.0) / 2.0, (top_left[1] + 1.0) / 2.0, y, True)

                uv = mathutils.Vector((x, y))

                if snap_mode == "to_corners":
                    uv = nUtil.find_closest_bound_vert(uv, mathutils.Vector(nUtil.abs_uv(top_left)), mathutils.Vector(nUtil.abs_uv(top_right)),
                                                       mathutils.Vector(nUtil.abs_uv(bottom_right)), nUtil.abs_uv(mathutils.Vector(bottom_left)))

                loop[uv_layer].uv = uv

            if normalize_to_bounds:
                if uv.x < uv_bounds_min.x: uv_bounds_min.x = uv.x
                if uv.y < uv_bounds_min.y: uv_bounds_min.y = uv.y

                if uv.x > uv_bounds_max.x: uv_bounds_max.x = uv.x
                if uv.y > uv_bounds_max.y: uv_bounds_max.y = uv.y

            itr += 1

        if normalize_to_bounds:
            # bounds aspect ratio
            uv_width = abs(uv_bounds_max.x - uv_bounds_min.x)
            uv_height = abs(uv_bounds_max.y - uv_bounds_min.y)
            aspect = uv_height / uv_width

            # normalize
            for loop in face.loops:
                uv = loop[uv_layer].uv

                factor_x = nMath.inverse_lerp(uv_bounds_min.x, uv_bounds_max.x, uv.x, True)
                factor_y = nMath.inverse_lerp(uv_bounds_min.y, uv_bounds_max.y, uv.y, True)

                if correct_aspect:
                    if aspect >= 1.0:
                        factor_x /= aspect
                    else:
                        factor_y *= aspect

                uv.x = nMath.lerp((rect.topLeftX + 1.0) / 2.0, (rect.topRightX + 1.0) / 2.0, factor_x, True)
                uv.y = nMath.lerp((rect.bottomLeftY + 1.0) / 2.0, (rect.topLeftY + 1.0) / 2.0, factor_y, True)


def unwrap_global(only_selected, context, mw, faces, unwrap_mode, correct_aspect, snap_mode, rect, uv_layer):
    """
    Unwraps the selected faces global to the sum of all faces
    """

    normalize_to_bounds = snap_mode != "off"

    if normalize_to_bounds:
        bounds_init = 1000000000
        uv_bounds_min = mathutils.Vector((bounds_init, bounds_init))
        uv_bounds_max = mathutils.Vector((-bounds_init, -bounds_init))

    ###############################################################
    # PASS 1 | Calculate global face transform
    ###############################################################
    selected_faces = []
    global_center = mathutils.Vector((0.0, 0.0, 0.0))
    global_tangent = mathutils.Vector((0.0, 0.0, 0.0))
    global_dir = mathutils.Vector((0.0, 0.0, 0.0))

    face_itr_count = 0
    for face in faces:
        if not face.select and only_selected: continue

        selected_faces.append(face)
        face_itr_count += 1

        # calculate face data
        center = mw @ mathutils.Vector(face.calc_center_median())
        normal = mw.inverted().transposed().to_3x3() @ mathutils.Vector(face.normal)
        tangent = mw.to_quaternion() @ face.calc_tangent_edge_pair()

        face_dir = (center + normal - center).normalized()

        # apply face data to global
        global_center += center
        global_tangent += tangent
        global_dir += face_dir

    # average face data
    global_center /= face_itr_count
    global_tangent /= face_itr_count
    global_dir /= face_itr_count

    # calculate global rotation
    unwrap_axis = bpy.context.scene.nuv_settings.unwrap_axis
    if unwrap_mode == "face":
        unwrap_up = global_tangent
    elif unwrap_mode == "world":
        unwrap_up = mathutils.Vector(unwrap_axis)
    elif unwrap_mode == "object":
        unwrap_up = mw.to_quaternion() @ mathutils.Vector(unwrap_axis)
    elif unwrap_mode == "camera":
        unwrap_up = context.space_data.region_3d.view_rotation @ mathutils.Vector(unwrap_axis)
    else:
        unwrap_up = global_tangent

    # calculate global matrix
    global_rot = nMath.axis_to_quat(global_dir, unwrap_up)

    global_rot_axis_angle = global_rot.to_axis_angle()
    global_matrix_loc = mathutils.Matrix.Translation((global_center.x, global_center.y, global_center.z))
    global_matrix_rot = mathutils.Matrix.Rotation(global_rot_axis_angle[1], 4, global_rot_axis_angle[0])
    global_matrix = global_matrix_loc @ global_matrix_rot

    ###############################################################
    # PASS 2 | Discover Max Dimensions
    ###############################################################
    max_dim_x = 0
    max_dim_y = 0

    linked_vert_data = []
    vert_count = 0
    for face in selected_faces:

        verts_local_center = []
        for vert in face.verts:
            vert_count += 1
            vert_world = mw @ vert.co
            vert_local_center = global_matrix.inverted() @ vert_world

            verts_local_center.append(vert_local_center)
            if abs(vert_local_center.x) > max_dim_x: max_dim_x = abs(vert_local_center.x)
            if abs(vert_local_center.y) > max_dim_y: max_dim_y = abs(vert_local_center.y)

        linked_vert_data.append(verts_local_center)

    # correct triangle dim
    if vert_count == 3:
        max_dim_x /= 2
        max_dim_y /= 2

    if correct_aspect:
        aspect = max_dim_x / max_dim_y

        if aspect >= 1:
            max_dim_y = max_dim_x
        else:
            max_dim_x = max_dim_y

    ###############################################################
    # PASS 3 | Unwrap Uvs
    ###############################################################
    face_itr = 0
    for face in selected_faces:
        verts_local_face = linked_vert_data[face_itr]

        itr = 0
        for loop in face.loops:

            # normalized to total uv space
            x = ((verts_local_face[itr].x / max_dim_x) + 1.0) / 2.0
            y = ((verts_local_face[itr].y / max_dim_y) + 1.0) / 2.0

            # scale down to rect
            top_left = nData.rect_top_left(rect)
            top_right = nData.rect_top_right(rect)
            bottom_left = nData.rect_bottom_left(rect)

            x = nMath.lerp((top_left[0] + 1.0) / 2.0, (top_right[0] + 1.0) / 2.0, x, True)
            y = nMath.lerp((bottom_left[1] + 1.0) / 2.0, (top_left[1] + 1.0) / 2.0, y, True)

            uv = mathutils.Vector((x, y))

            loop[uv_layer].uv = uv

            if normalize_to_bounds:
                if uv.x < uv_bounds_min.x: uv_bounds_min.x = uv.x
                if uv.y < uv_bounds_min.y: uv_bounds_min.y = uv.y

                if uv.x > uv_bounds_max.x: uv_bounds_max.x = uv.x
                if uv.y > uv_bounds_max.y: uv_bounds_max.y = uv.y

            itr += 1

        face_itr += 1

    ###############################################################
    # PASS 4 | Normalize
    ###############################################################
    if normalize_to_bounds:
        for face in selected_faces:
            # bounds aspect ratio
            uv_width = abs(uv_bounds_max.x - uv_bounds_min.x)
            uv_height = abs(uv_bounds_max.y - uv_bounds_min.y)
            aspect = uv_height / uv_width

            # normalize
            for loop in face.loops:
                uv = loop[uv_layer].uv

                factor_x = nMath.inverse_lerp(uv_bounds_min.x, uv_bounds_max.x, uv.x, True)
                factor_y = nMath.inverse_lerp(uv_bounds_min.y, uv_bounds_max.y, uv.y, True)

                if correct_aspect:
                    if aspect >= 1.0:
                        factor_x /= aspect
                    else:
                        factor_y *= aspect

                uv.x = nMath.lerp((rect.topLeftX + 1.0) / 2.0, (rect.topRightX + 1.0) / 2.0, factor_x, True)
                uv.y = nMath.lerp((rect.bottomLeftY + 1.0) / 2.0, (rect.topLeftY + 1.0) / 2.0, factor_y, True)

# endregion

# region Mesh Operators


class UtilOpMeshOperator(bpy.types.Operator):
    def invoke(self, context, event):

        # make sure the current contet is a mesh
        t = bpy.context.object.type
        if t != 'MESH': return {'FINISHED'}

        if bpy.context.active_object.mode == "OBJECT": return {'FINISHED'}

        bpy.ops.ed.undo_push(message="NeoTileMap Mesh Operation")

        # run pre edit
        self.pre_edit(context, event)

        # prepare bmesh
        in_edit_mode = bpy.context.object.mode == 'EDIT'

        mesh = bpy.context.object.data
        bm = bmesh.new() if not in_edit_mode else bmesh.from_edit_mesh(mesh)
        if not in_edit_mode: bm.from_mesh(mesh)

        # run mesh edit
        self.do_mesh_edit(context, event, bm, in_edit_mode)

        # free bmesh
        if not in_edit_mode:
            bm.to_mesh(mesh)
            bm.free()
        else:
            bmesh.update_edit_mesh(mesh)

        # run post edit
        self.post_edit(context, event)

        return {'FINISHED'}

    def pre_edit(self, context, event):
        pass

    def do_mesh_edit(self, context, event, bm, in_edit_mode):
        pass

    def post_edit(self, context, event):
        pass


class UtilOpNeoSetUvRect(UtilOpMeshOperator):
    """Unwraps UVs based on a provided UV rectangle."""
    bl_idname = "neo.uv_setuvrect"
    bl_label = "Set Uv Rect"
    bl_description = "Unwraps the selected faces to the selected rect."

    collectionIdx: bpy.props.IntProperty(name="Collection Index")
    rectIdx: bpy.props.IntProperty(name="Rect Index")

    def do_mesh_edit(self, context, event, bm, in_edit_mode):

        # get variables
        space_mode = bpy.context.scene.nuv_settings.mode_space
        unwrap_mode = bpy.context.scene.nuv_settings.mode_unwrap
        correct_aspect = bpy.context.scene.nuv_settings.correct_aspect_ratio
        snap_mode = bpy.context.scene.nuv_settings.snap_mode
        collection = bpy.context.scene.nuv_uvSets[self.collectionIdx]
        rect = collection.items[self.rectIdx]

        # parent object data
        obj = bpy.context.object
        mw = obj.matrix_world

        # get active uv layer
        layer = bm.loops.layers.uv
        uv_layer = layer.verify()

        unwrap_auto(space_mode, in_edit_mode, context, mw, bm.faces, unwrap_mode, correct_aspect, snap_mode, rect,
                    uv_layer)


class UtilOpNeoSetUvRectNormal(UtilOpMeshOperator):
    """Unwraps UVs to a 0-1 range."""
    bl_idname = "neo.uv_setuvrectnormal"
    bl_label = "Set Uv Rect (Normalized)"
    bl_description = "Unwraps the selected faces to a normalzed 0-1 uv range."

    def do_mesh_edit(self, context, event, bm, in_edit_mode):

        # get variables
        space_mode = bpy.context.scene.nuv_settings.mode_space
        unwrap_mode = bpy.context.scene.nuv_settings.mode_unwrap
        correct_aspect = bpy.context.scene.nuv_settings.correct_aspect_ratio
        snap_mode = bpy.context.scene.nuv_settings.snap_mode

        # create dummy rect
        rect = nData.NeoRect((-1, 1), (1, 1), (-1, -1), (1, -1))

        # parent object data
        obj = bpy.context.object
        mw = obj.matrix_world

        # get active uv layer
        layer = bm.loops.layers.uv
        uv_layer = layer.verify()

        unwrap_auto(space_mode, in_edit_mode, context, mw, bm.faces, unwrap_mode, correct_aspect, snap_mode, rect,
                    uv_layer)


class UtilOpNeoPaintUnwrap(bpy.types.Operator):
    bl_idname = "neo.uv_paintunwrap"
    bl_label = "Paint Unwrap"
    bl_description = "Paint the selected rect onto faces"

    collectionIdx: bpy.props.IntProperty()
    rectIdx: bpy.props.IntProperty()

    def invoke(self, context, event):
        bpy.ops.view3d.nuv_paint("INVOKE_DEFAULT", collectionIdx=self.collectionIdx, rectIdx=self.rectIdx)
        return {"FINISHED"}


class UtilOpNeoPatternUnwrap(UtilOpMeshOperator):
    bl_idname = "neo.uv_patternunwrap"
    bl_label = "Pattern Unwrap"
    bl_description = "Applies the pattern randomly to all selected faces."

    collectionIdx: bpy.props.IntProperty()

    def do_mesh_edit(self, context, event, bm, in_edit_mode):
        # get variables
        space_mode = bpy.context.scene.nuv_settings.mode_space
        unwrap_mode = bpy.context.scene.nuv_settings.mode_unwrap
        correct_aspect = bpy.context.scene.nuv_settings.correct_aspect_ratio
        snap_mode = bpy.context.scene.nuv_settings.snap_mode
        collection = bpy.context.scene.nuv_uvSets[self.collectionIdx]
        pattern = collection.get_active_pattern()

        items = pattern.items.items()
        pattern_len = len(items)

        # parent object data
        obj = bpy.context.object
        mw = obj.matrix_world

        # get active uv layer
        layer = bm.loops.layers.uv
        uv_layer = layer.verify()

        for face in bm.faces:
            idx = random.randrange(0, pattern_len)

            pattern_rect = items[idx][1]

            if pattern_rect.rect_idx < 0:
                continue

            rect = pattern_rect.get_rect(collection)

            unwrap_local(in_edit_mode, context, mw, {face}, unwrap_mode, correct_aspect, snap_mode,
                        rect, uv_layer)


class UtilOpNeoRotUv(UtilOpMeshOperator):
    bl_idname = "neo.uv_rot"
    bl_label = "Rotate UV"
    bl_description = "Rotates the UV."

    clockwise: bpy.props.BoolProperty()

    def do_mesh_edit(self, context, event, bm, in_edit_mode):

        # get active uv layer
        layer = bm.loops.layers.uv
        uv_layer = layer.verify()

        rotate(in_edit_mode, bm.faces, self.clockwise, uv_layer)


class UtilOpNeoFlipUv(UtilOpMeshOperator):
    bl_idname = "neo.uv_flip"
    bl_label = "Flip UV"
    bl_description = "Flips the UV."

    horizontal: bpy.props.BoolProperty()

    def do_mesh_edit(self, context, event, bm, in_edit_mode):

        # get active uv layer
        layer = bm.loops.layers.uv
        uv_layer = layer.verify()

        flip(in_edit_mode, bm.faces, self.horizontal, uv_layer)


class UtilOpNeoNormalizeUv(UtilOpMeshOperator):
    bl_idname = "neo.uv_normalize"
    bl_label = "Normalize UV"
    bl_description = "Normalizes the selected UVs so that they stretch to fill the whole 0-1 UV range."

    def do_mesh_edit(self, context, event, bm, in_edit_mode):

        correct_aspect = bpy.context.scene.nuv_settings.correct_aspect_ratio

        # get active uv layer
        layer = bm.loops.layers.uv
        uv_layer = layer.verify()

        bounds_init = 1000000000
        uv_bounds_min = mathutils.Vector((bounds_init, bounds_init))
        uv_bounds_max = mathutils.Vector((-bounds_init, -bounds_init))

        # calculate uv bounds
        for face in bm.faces:
            if not face.select and in_edit_mode: continue

            # enumerate uvs and update uv bounds
            for vert, loop in zip(face.verts, face.loops):
                uv = loop[uv_layer].uv

                if uv.x < uv_bounds_min.x: uv_bounds_min.x = uv.x
                if uv.y < uv_bounds_min.y: uv_bounds_min.y = uv.y

                if uv.x > uv_bounds_max.x: uv_bounds_max.x = uv.x
                if uv.y > uv_bounds_max.y: uv_bounds_max.y = uv.y

        # calculate aspect ratio
        uv_width = abs(uv_bounds_max.x - uv_bounds_min.x)
        uv_height = abs(uv_bounds_max.y - uv_bounds_min.y)
        aspect = uv_height / uv_width

        # normalize the uvs
        for face in bm.faces:
            if not face.select and in_edit_mode: continue

            for vert, loop in zip(face.verts, face.loops):
                uv = loop[uv_layer].uv
                uv.x = nMath.inverse_lerp(uv_bounds_min.x, uv_bounds_max.x, uv.x, True)
                uv.y = nMath.inverse_lerp(uv_bounds_min.y, uv_bounds_max.y, uv.y, True)

                if correct_aspect:
                    if aspect >= 1.0:
                        uv.x /= aspect
                    else:
                        uv.y *= aspect

                loop[uv_layer].uv = mathutils.Vector(uv)


# endregion

# region User Action Operators


class UilOpNeoRepeatSelectUv(bpy.types.Operator):
    bl_idname = "neo.uv_repeatselectuv"
    bl_label = "Repeat Select UV"
    bl_description = "Repeats a select and unwrap from the last used collection. Assign this a hotkey!"

    def invoke(self, context, event):
        last_set = bpy.context.scene.nuv_settings.last_uv_set
        if last_set < 0:
            return {"CANCELLED"}

        collection_list = bpy.context.scene.nuv_uvSets
        if len(collection_list) < 1:
            return {"CANCELLED"}

        bpy.ops.view3d.nuv_set_uv_rect_selector('INVOKE_DEFAULT',
                                                collectionIdx=bpy.context.scene.nuv_settings.last_uv_set)
        return {"FINISHED"}


class UtilOpNeoRepeatPaintUv(bpy.types.Operator):
    bl_idname = "neo.uv_repeatpaintuv"
    bl_label = "Repeat Paint UV"
    bl_description = "Repeats the paint UV operator using the last used collection. Assign this a hotkey!"

    def invoke(self, context, event):
        last_set = bpy.context.scene.nuv_settings.last_uv_set
        if last_set < 0:
            return {"CANCELLED"}

        collection_list = bpy.context.scene.nuv_uvSets
        if len(collection_list) < 1:
            return {"CANCELLED"}

        bpy.ops.view3d.nuv_set_paint_rect_selector('INVOKE_DEFAULT',
                                                collectionIdx=bpy.context.scene.nuv_settings.last_uv_set)
        return {"FINISHED"}


class UtilOpNeoUvReload(bpy.types.Operator):
    bl_idname = "neo.uv_uireload"
    bl_label = "Reload"
    bl_description = "Reloads the tilemap from disk."

    collectionIdx: bpy.props.IntProperty()
    def invoke(self, context, event):
        path = bpy.context.scene.nuv_uvSets[self.collectionIdx].relative_path
        path = os.path.abspath(path)

        if not os.path.exists(path):
            self.report({"ERROR"}, "The file \"" + path + "\" no longer exists.")
            return {"CANCELLED"}

        report = nData.ImportRectData.import_file(path)
        for r in report:
            if r == "CANCELLED":
                self.report({"ERROR"}, "Not a valid tile map project file.")

        print("Reloaded Tile Map: " + path)
        return report

# endregion

# region Blender


classes = (
    UtilOpNeoSetUvRect,
    UilOpNeoRepeatSelectUv,
    UtilOpNeoUvReload,
    UtilOpNeoRotUv,
    UtilOpNeoFlipUv,
    UtilOpNeoNormalizeUv,
    UtilOpNeoSetUvRectNormal,
    UtilOpNeoPaintUnwrap,
    UtilOpNeoPatternUnwrap,
    UtilOpNeoRepeatPaintUv,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
# endregion