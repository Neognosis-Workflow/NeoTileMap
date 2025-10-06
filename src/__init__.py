# region Imports

from importlib import reload
import bpy
from . import nData
from . import nMath
from . import nInterface
from . import nUv
from . import nImageOp
from . import nRectOps
from . import nInteractiveUv
from . import nUtil
import inspect

# endregion

# region Data

class VIEW3D_PT_NeoTmPanel(bpy.types.Panel):
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
        scene = context.scene
        obj = context.object

        row = layout.row(align=True)
        nInterface.ui_draw(layout, context)
        return

# endregion

# region Blender

bl_info = {
    "name" : "Neognosis Tile Mapper",
    "author" : "Adam Chivers",
    "description" : "",
    "blender" : (2, 90, 0),
    "version" : (1, 3),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

classes = (
    VIEW3D_PT_NeoTmPanel,
)

modules = (
    nData,
    nInterface,
    nMath,
    nUv,
    nImageOp,
    nRectOps,
    nInteractiveUv,
    nUtil,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
        
    for m in modules:
        reload(m)
        if hasattr(m, "register"):
            m.register()


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    for m in modules:
        if hasattr(m, "unregister"):
            m.unregister()


if __name__ == '__main__':
    register()

# endregion
