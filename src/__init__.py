from importlib import reload
import bpy
from . import nTileStorage
from . import nMath
from . import nTileUi
from . import nUvTools
from . import nImageEditor
from . import nInteractiveRectSelector
from . import nInteractiveUv
from . import nUtil

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
        nTileUi.draw_tile_set_ui(layout, context)
        return


classes = (
    VIEW3D_PT_NeoTmPanel,
)

modules = (
    nTileStorage,
    nTileUi,
    nMath,
    nUvTools,
    nImageEditor,
    nInteractiveRectSelector,
    nInteractiveUv,
    nUtil,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
        
    for m in modules:
        reload(m)
        m.register()


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    for m in modules:
        m.unregister()

if __name__ == '__main__':
    register()