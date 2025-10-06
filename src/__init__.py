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
from . import nPaint
from . import nPatternPaint
import inspect

# endregion

# region Blender


bl_info = {
    "name" : "Neognosis Tile Mapper",
    "author" : "Adam Chivers",
    "description" : "",
    "blender" : (2, 90, 0),
    "version" : (1, 4),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

modules = (
    nData,
    nInterface,
    nMath,
    nUv,
    nImageOp,
    nRectOps,
    nInteractiveUv,
    nPaint,
    nPatternPaint,
    nUtil,
)


def register():
    for m in modules:
        reload(m)
        if hasattr(m, "register"):
            m.register()


def unregister():
    for m in modules:
        if hasattr(m, "unregister"):
            m.unregister()


if __name__ == '__main__':
    register()

# endregion
