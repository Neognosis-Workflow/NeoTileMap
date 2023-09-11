#region Imports
import bpy
import os
import tempfile
import struct
from bpy_extras.io_utils import ImportHelper
from pathlib import Path
from bpy.props import *
#endregion

#region Property Groups

class NeoTileRect(bpy.types.PropertyGroup):
    """Contains data for a UV rect.
    """

    previewName: StringProperty(name="Preview Name")

    topLeftX: FloatProperty(name="Top Left X")
    topLeftY: FloatProperty(name="Top Left Y")

    topRightX: FloatProperty(name="Top Right X")
    topRightY: FloatProperty(name="Top Right Y")

    bottomLeftX: FloatProperty(name="Bottom Left X")
    bottomLeftY: FloatProperty(name="Bottom Left Y")

    bottomRightX: FloatProperty(name="Bottom Right X")
    bottomRightY: FloatProperty(name="Bottom Right Y")

    def topLeft(self):
        return [self.topLeftX, self.topLeftY]

    def topRight(self):
        return [self.topRightX, self.topRightY]

    def bottomRight(self):
        return [self.bottomRightX, self.bottomRightY]

    def bottomLeft(self):
        return [self.bottomLeftX, self.bottomLeftY]

class NeoTileRectCollection(bpy.types.PropertyGroup):
    """Contains data for a collection of rects.
    """
    name: StringProperty(name="Name")
    relative_path: StringProperty(name="Path")
    items: CollectionProperty(type=NeoTileRect)
    expanded: BoolProperty(name="Expanded")
    items_expanded: BoolProperty(name="Items Expanded")
    page: IntProperty(name="Page", min=0, max=10)

    def clear(self):
        self.items.clear()

class NeoTileDeleteCollection(bpy.types.Operator):
    bl_idname = "neo.uvset_delete"
    bl_label = "Delete"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()

    def invoke(self, context, event):

        bpy.ops.ed.undo_push(message="Delete NeoTileMap")
        col_list = bpy.context.scene.nuv_uvSets
        col_list.remove(self.collectionIdx)

        return {'FINISHED'}

#endregion

#region Import Classes
class ImportRectData(bpy.types.Operator, ImportHelper):
    """Import handler and methods for importing rect data from the tilemap builder tool
    """

    bl_idname = "import_tileset.tmprj"
    bl_label = "Import Neo Tile Set"
    filename_ext = ".tmprj"

    filter_glob: bpy.props.StringProperty(
        default="*.tmprj",
        options={'HIDDEN'}
    )

    @staticmethod
    def addImage(f, n):
        """Adds an image to the blend file, replacing it if it already exists.

        Args:
            f (str): The filepath of the image to add.
            n (str): The name to give the image in the blend file
        """

        # delete image if it already exists
        for i in bpy.data.images:
            if i.name == n:
                i.filepath = f
                i.reload()
                i.pack()
                i.use_fake_user = True

                return

        image = bpy.data.images.load(f)
        image.name = n
        image.reload()
        image.pack()
        image.use_fake_user = True

    @staticmethod
    def addCollection(n, filePath):
        """Adds or discovers a new uv tile set collection to the blender scene.

        Args:
            n (str): The name to give the collection.

        Returns:
            NeoTileRectCollection: The collection that was created or discovered.
        """

        collectionList = bpy.context.scene.nuv_uvSets

        for i in range(0, len(collectionList)):
            collection = collectionList[i]
            if collection.name == n:
                collection.relative_path = filePath
                return collection

        newSet = bpy.context.scene.nuv_uvSets.add()
        newSet.name = n
        newSet.relative_path = filePath

        return newSet

    @staticmethod
    def clearCollection(n):
        """Clears all items from the collection with the given name.

        Args:
            n (str): The name of the collection to clear items from.
        """
        collectionList = bpy.context.scene.nuv_uvSets

        for i in range(0, len(collectionList)):
            collection = collectionList[i]
            if collection.name == n:
                collection.clear()

    @staticmethod
    def rectVertsCompare(a, verts):
        """Compares a rects vertices to the provided vertex array to determine if they are the same.

        Args:
            a (NeoTileRect): The rect to compare the array to.
            verts (array): The array of vertices to use in the comparison.

        Returns:
            boolean: Whether the rect and vertex array succesfully compare.
        """

        return (a.topLeftX == verts[0][0] and a.topLeftY == verts[0][1]
            and a.topRightX == verts[1][0] and a.topRightY == verts[1][1]
            and a.bottomLeftX == verts[2][0] and a.bottomLeftY == verts[2][1]
            and a.bottomRightX == verts[3][0] and a.bottomRightY == verts[3][1])

    @staticmethod
    def addRectToCollection(verts, imgName, c):
        """Adds a rect to a given collection

        Args:
            verts (array): The array of vertices that make up the rect.
            imgName (str): The name of the image to assign as the rect preview.
            c (NeoTileRectCollection): The collection to add the rect to.
        """

        for t in c.items:
            if ImportRectData.rectVertsCompare(t, verts):
                ImportRectData.setupRect(verts, imgName, t)
                return

        newRect = c.items.add()
        ImportRectData.setupRect(verts, imgName, newRect)

    @staticmethod
    def setupRect(verts, imgName, t):
        """Configures a rect.

        Args:
            verts (array): The array of vertices to use in the rect.
            imgName (str): The name of the image to use as the rects preview icon.
            t (NeoTileRect): The tile rect to configure.
        """

        t.previewName = imgName
        t.topLeftX = verts[0][0]
        t.topLeftY = verts[0][1]

        t.topRightX = verts[1][0]
        t.topRightY = verts[1][1]

        t.bottomRightX = verts[2][0]
        t.bottomRightY = verts[2][1]

        t.bottomLeftX = verts[3][0]
        t.bottomLeftY = verts[3][1]

    @staticmethod
    def toVerts(topLeftX, topLeftY, topRightX, topRightY, bottomRightX, bottomRightY, bottomLeftX, bottomLeftY):
        """Takes a series of split vertex elements and joins them into a multidimensional array for convient access
        """

        return [[topLeftX, topLeftY], [topRightX, topRightY], [bottomRightX, bottomRightY], [bottomLeftX, bottomLeftY]]

    @staticmethod
    def importFile(filepath):
        try:
            relpath = os.path.relpath(filepath)
        except:
            relpath = filepath

        with open(filepath, "rb") as f:
            bOrd = 'little'

            fileLen = os.path.getsize(filepath)
            loadedcontent = []

            # read header
            idLen = int.from_bytes(f.read(1), byteorder=bOrd, signed=False)
            idName = f.read(idLen).decode("utf-8")

            if idName != "NEOPROJ":
                return {'CANCELLED'}

            # version
            version = int.from_bytes(f.read(4), byteorder=bOrd, signed=False)

            # load data
            while f.tell() < fileLen:
                newContent = ProjectFileContent(f)
                loadedcontent.append(newContent)

                currPos = f.tell()
                f.seek(currPos + newContent.dataLen)

            # process data
            for c in loadedcontent:
                f.seek(c.dataAddress)

                if c.name == "atlas":
                    # not needed for blender loading
                    tileWidth = int.from_bytes(f.read(4), byteorder=bOrd, signed=True)
                    tileHeight = int.from_bytes(f.read(4), byteorder=bOrd, signed=True)

                    pngLen = int.from_bytes(f.read(4), byteorder=bOrd, signed=True)
                    pngBytes = f.read(pngLen)

                    # save atlas to a temp location and then reload it
                    imgName = Path(filepath).stem
                    imgPath = os.path.join(os.path.dirname(filepath), imgName + "_atlas.png")

                    with open(imgPath, mode="wb") as atlasF:
                        atlasF.write(pngBytes)

                    ImportRectData.addImage(imgPath, "Atlas_" + imgName)

                    # we're done with the file, remove it
                    if os.path.exists(imgPath): os.remove(imgPath)
                elif c.name == "uvs":
                    rectCount = int.from_bytes(f.read(4), byteorder=bOrd, signed=True)

                    # clear the collection if it already exists
                    imgName = Path(filepath).stem
                    ImportRectData.clearCollection(imgName)

                    for i in range(0, rectCount):
                        # uv vertex positions
                        topLeftX = struct.unpack('f', f.read(4))[0]
                        topLeftY = struct.unpack('f', f.read(4))[0]

                        topRightX = struct.unpack('f', f.read(4))[0]
                        topRightY = struct.unpack('f', f.read(4))[0]

                        bottomRightX = struct.unpack('f', f.read(4))[0]
                        bottomRightY = struct.unpack('f', f.read(4))[0]

                        bottomLeftX = struct.unpack('f', f.read(4))[0]
                        bottomLeftY = struct.unpack('f', f.read(4))[0]

                        # preview texture data
                        pngLen = int.from_bytes(f.read(4), byteorder=bOrd, signed=True)
                        pngBytes = f.read(pngLen)

                        imgPath = os.path.join(os.path.dirname(filepath), imgName + "_preview.png")

                        with open(imgPath, mode="wb") as previewF:
                            previewF.write(pngBytes)

                        previewName = ".Atlas_" + imgName + "_Preview" + str(i)
                        ImportRectData.addImage(imgPath, previewName)

                        # we're done with the file, remove it
                        if os.path.exists(imgPath): os.remove(imgPath)

                        # create collection item
                        verts = ImportRectData.toVerts(topLeftX, topLeftY,
                            topRightX, topRightY,
                            bottomRightX, bottomRightY,
                            bottomLeftX, bottomLeftY)

                        collection = ImportRectData.addCollection(imgName, relpath)
                        ImportRectData.addRectToCollection(verts, previewName, collection)
        return {'FINISHED'}


    def execute(self, context):
            report = self.importFile(self.properties.filepath)
            for r in report:
                if r == "CANCELLED":
                    self.report({"ERROR"}, "Not a valid tile map project file.")

            return report


class ProjectFileContent:
    """Contains data read from a neognosisi project file.
    """

    def __init__(self, f):
        nameLen = int.from_bytes(f.read(1), byteorder='little', signed=False)
        self.name = f.read(nameLen).decode('utf-8')
        self.dataLen = int.from_bytes(f.read(8), byteorder='little', signed=True)
        self.dataAddress = f.tell()

#endregion

#region Blender
classes = (
    ImportRectData,
    NeoTileRect,
    NeoTileRectCollection,
    NeoTileDeleteCollection
)

def menu_import(self, context):
    self.layout.operator(ImportRectData.bl_idname, text = "Neognosis Tile Set (.tmprj)")

def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    setupProps()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    desetupProps()

def setupProps():
    bpy.types.Scene.nuv_uvSets = bpy.props.CollectionProperty(type=NeoTileRectCollection)

def desetupProps():
    pass
#endregion
