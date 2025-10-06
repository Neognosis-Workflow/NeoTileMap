"""Contains helper methods for math"""

# region Imports

import mathutils
import math

#endregion

# region Methods

def inverse_lerp(a, b, v, clamp):
    """Returns V as the T value between A and B."""

    if a == b:
        return 0

    result = (v - a) / (b - a)

    if clamp:
        if result > 1:
            result = 1
        if result < 0:
            result = 0

    return result


def lerp(a, b, t, clamp):
    """Returns the linearly interpoled value between A and B using T."""
    if clamp:
        if t > 1:
            t = 1
        if t < 0:
            t = 0

    return a + (b - a) * t


def axis_to_quat(forward, up):
    """Creates a quaternion using a forward and up vector.

    Args:
        forward (Vector): The forward vector that describes the direction of the rotation.
        up (Vector): The up vector that describes the frame of reference for the rotation.

    Returns:
        Quaternion: The generated rotation.
    """
    v = forward
    v.normalize()
    v2 = up.cross(v)
    v2.normalize()
    v3 = v.cross(v2)
    v3.normalize()

    m00 = v2.x
    m01 = v2.y
    m02 = v2.z
    m10 = v3.x
    m11 = v3.y
    m12 = v3.z
    m20 = v.x
    m21 = v.y
    m22 = v.z

    num8 = (m00 + m11) + m22
    quaternion = mathutils.Quaternion()
    if num8 > 0.0:
        num = math.sqrt(num8 + 1.0)
        quaternion.w = num * 0.5
        num = 0.5 / num
        quaternion.x = (m12 - m21) * num
        quaternion.y = (m20 - m02) * num
        quaternion.z = (m01 - m10) * num
        return quaternion
    if (m00 >= m11) and (m00 >= m22):
        num7 = math.sqrt(((1.0 + m00) - m11) - m22)
        num4 = 0.5 / num7
        quaternion.x = 0.5 * num7
        quaternion.y = (m01 + m10) * num4
        quaternion.z = (m02 + m20) * num4
        quaternion.w = (m12 - m21) * num4
        return quaternion
    if m11 > m22:
        num6 = math.sqrt(((1.0 + m11) - m00) - m22)
        num3 = 0.5 / num6
        quaternion.x = (m10 + m01) * num3
        quaternion.y = 0.5 * num6
        quaternion.z = (m21 + m12) * num3
        quaternion.w = (m20 - m02) * num3
        return quaternion

    num5 = math.sqrt(((1.0 + m22) - m00) - m11)
    num2 = 0.5 / num5
    quaternion.x = (m20 + m02) * num2
    quaternion.y = (m21 + m12) * num2
    quaternion.z = 0.5 * num5
    quaternion.w = (m01 - m10) * num2
    return quaternion


def rotate_vector(v, o, angle):

    angle = math.radians(angle)

    # get sin and cosine of angle
    s = math.sin(angle)
    c = math.cos(angle)

    # move vector back to origin
    v.x -= o.x
    v.y -= o.y

    # rotate the point
    new_x = v.x * c - v.y * s
    new_y = v.x * s + v.y * c

    # move vector out
    v.x = new_x + o.x
    v.y = new_y + o.y

    return v


def center_for_triangle(a, b, c):
    dist_a_b = dist_2d(a, b)
    dist_b_c = dist_2d(b, c)
    dist_c_a = dist_2d(c, a)

    if dist_a_b > dist_b_c:
        return mathutils.Vector(((a.x + b.x) / 2, (a.y + b.y) / 2))
    elif dist_b_c > dist_c_a:
        return mathutils.Vector(((b.x + c.x) / 2, (b.y + c.y) / 2))
    else:
        return mathutils.Vector(((c.x + a.x) / 2, (c.y + a.y) / 2))


def calculate_uv_from_raycast(hit_loc, face, uv_layer):
    verts = []
    for v in face.verts:
        verts.append(v.co)

    weights = mathutils.interpolate.poly_3d_calc(verts, hit_loc)

    uv = mathutils.Vector((0.0, 0.0))
    for i in range(len(weights)):
        uv += weights[i] * face.loops[i][uv_layer].uv

    return uv


def calculate_uv_from_raycast_custom_verts(hit_loc, face, verts, uv_layer):
    weights = mathutils.interpolate.poly_3d_calc(verts, hit_loc)

    uv = mathutils.Vector((0.0, 0.0))
    for i in range(len(weights)):
        uv += weights[i] * face.loops[i][uv_layer].uv

    return uv


def dist_2d(a, b):
    return (a - b).magnitude

# endregion
