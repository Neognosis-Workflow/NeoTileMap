# region Imports

import bpy
import os
import tempfile
import struct
import math
from bpy_extras.io_utils import ImportHelper
from pathlib import Path
from bpy.props import *

# endregion

# region Rect Methods


def rect_contains(rect, x, y):
    return (rect.topLeftX + 1) / 2 < x < (rect.topRightX + 1) / 2 and (rect.bottomLeftY + 1) / 2 < y < (rect.topLeftY + 1) / 2


def rect_top_left(rect):
    return [rect.topLeftX, rect.topLeftY]


def rect_top_right(rect):
    return [rect.topRightX, rect.topRightY]


def rect_bottom_left(rect):
    return [rect.bottomLeftX, rect.bottomLeftY]


def rect_bottom_right(rect):
    return [rect.bottomRightX, rect.bottomRightY]


def copy_rect(a, b):
    """Copies the vertex positions of Aect A into Rect B."""
    b.topLeftX = a.topLeftX
    b.topLeftY = a.topLeftY

    b.topRightX = a.topRightX
    b.topRightY = a.topRightY

    b.bottomLeftX = a.bottomLeftX
    b.bottomLeftY = a.bottomLeftY

    b.bottomRightX = a.bottomRightX
    b.bottomRightY = a.bottomRightY


def rect_to_tuples(rect):
    """Returns a rect as an array of tuples in order of Top Left, Top Right, Bottom Left and Bottom Right"""
    return [(rect.topLeftX, rect.topLeftY),
            (rect.topRightX, rect.topRightY),
            (rect.bottomLeftX, rect.bottomLeftY),
            (rect.bottomRightX, rect.bottomRightY)]


def are_rects_same(a, b):
    """Returns true if Rect A and Rect B have the same vertex positions"""
    return (
            math.isclose(a.topLeftX, b.topLeftX)
            and math.isclose(a.topLeftY, b.topLeftY)
            and math.isclose(a.topRightX, b.topRightX)
            and math.isclose(a.topRightY, b.topRightY)
            and math.isclose(a.bottomLeftX, b.bottomLeftX)
            and math.isclose(a.bottomLeftY, b.bottomLeftY)
            and math.isclose(a.bottomRightX, b.bottomRightX)
            and math.isclose(a.bottomRightY, b.bottomRightY)
    )

# endregion

# region Collection Methods


def get_collections():
    return bpy.context.scene.nuv_uvSets


def get_collection_by_idx(idx):
    return bpy.context.scene.nuv_uvSets[idx]


# endregion

# region Property Groups


class NeoRect:
    """Contains data for a UV rect."""
    def __init__(self, top_left, top_right, bottom_left, bottom_right):
        self.topLeftX = top_left[0]
        self.topLeftY = top_left[1]

        self.topRightX = top_right[0]
        self.topRightY = top_right[1]

        self.bottomLeftX = bottom_left[0]
        self.bottomLeftY = bottom_left[1]

        self.bottomRightX = bottom_right[0]
        self.bottomRightY = bottom_right[1]


class NeoTileRect(bpy.types.PropertyGroup):
    """Contains data for a UV rect and preview image as a Blender type."""

    previewName: StringProperty(name="Preview Name")

    topLeftX: FloatProperty(name="Top Left X")
    topLeftY: FloatProperty(name="Top Left Y")

    topRightX: FloatProperty(name="Top Right X")
    topRightY: FloatProperty(name="Top Right Y")

    bottomLeftX: FloatProperty(name="Bottom Left X")
    bottomLeftY: FloatProperty(name="Bottom Left Y")

    bottomRightX: FloatProperty(name="Bottom Right X")
    bottomRightY: FloatProperty(name="Bottom Right Y")

    def apply_tuples(self, top_left_vert, top_right_vert, bottom_left_vert, bottom_right_vert):
        self.topLeftX = top_left_vert[0]
        self.topLeftY = top_left_vert[1]

        self.topRightX = top_right_vert[0]
        self.topRightY = top_right_vert[1]

        self.bottomLeftX = bottom_left_vert[0]
        self.bottomLeftY = bottom_left_vert[1]

        self.bottomRightX = bottom_right_vert[0]
        self.bottomRightY = bottom_right_vert[1]


class NeoTilePatternEntry(NeoTileRect):
    rect_idx: IntProperty(default=-1)

    def try_discover_rect_idx(self, collection):
        items = collection.items.items()
        items_len = len(items)

        self.rect_idx = -1
        for i in range(items_len):
            rect = items[i][1]

            if are_rects_same(self, rect):
                self.rect_idx = i
                return

    def get_rect(self, collection):
        items = collection.items.items()

        if -1 < self.rect_idx < len(items): return items[self.rect_idx][1]
        return None


class NeoTileRectPattern(bpy.types.PropertyGroup):
    name: StringProperty(default="Pattern")
    items: CollectionProperty(type=NeoTilePatternEntry)
    use_random: BoolProperty(default=False, description="Whether the pattern will be painted randomly instead of sequentially.")
    reset_stroke_on_click: BoolProperty(default=True, description="Whether the pattern index will be reset when starting a new stroke. When shift is held, this option will be inverted.")
    allow_repaint: BoolProperty(default=True, description="Whether faces that have already been painted can be painted on again.")

    def update_pattern_indicies(self, collection):
        for item in self.items:
            item.try_discover_rect_idx(collection)

    def add_rect(self):
        self.items.add()

    def set_rect(self, collection_idx, item_idx, rect_idx):
        items = self.items.items()

        collection = get_collection_by_idx(collection_idx)

        rect = collection.get_rect(rect_idx)
        pattern_rect = items[item_idx][1]
        pattern_rect.rect_idx = rect_idx

        copy_rect(rect, pattern_rect)

    def delete_rect(self, pattern_rect_idx):
        self.items.remove(pattern_rect_idx)


class NeoTileRectCollection(bpy.types.PropertyGroup):
    """Contains data for a collection of rects.
    """
    name: StringProperty(name="Name")
    relative_path: StringProperty(name="Path")
    items: CollectionProperty(type=NeoTileRect)
    patterns: CollectionProperty(type=NeoTileRectPattern)
    active_pattern: IntProperty(default=-1)
    expanded: BoolProperty(name="Expanded")
    items_expanded: BoolProperty(name="Items Expanded")
    patterns_expanded: BoolProperty(name="Patterns Expanded")
    page: IntProperty(name="Page", min=0, max=10)

    def add_pattern(self):
        self.patterns.add()
        self.active_pattern = len(self.patterns.items()) - 1

    def remove_pattern(self):
        items = self.patterns.items()
        items_len = len(items)

        if -1 < self.active_pattern < items_len:
            self.patterns.remove(self.active_pattern)

        items_len -= 1

        if self.active_pattern > items_len - 1:
            self.active_pattern = items_len - 1

    def get_active_pattern(self):
        if self.active_pattern < 0:
            return None

        items = self.patterns.items()
        if self.active_pattern > len(items) - 1:
            return None

        return items[self.active_pattern][1]

    def update_pattern_indicies(self):
        for p in self.patterns:
            p.update_pattern_indicies(self)

    def get_rect(self, rect_idx):
        items = self.items.items()
        return items[rect_idx][1]

    def clear(self):
        self.items.clear()

# endregion

# region Operators


class NeoTileAddPattern(bpy.types.Operator):
    bl_idname = "neo.uvset_add_pattern"
    bl_label = "Add Pattern"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()

    def invoke(self, context, event):

        bpy.ops.ed.undo_push(message="Add Pattern")
        get_collection_by_idx(self.collectionIdx).add_pattern()

        return {'FINISHED'}


class NeoTileDeletePattern(bpy.types.Operator):
    bl_idname = "neo.uvset_delete_pattern"
    bl_label = "Delete Pattern"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()

    def invoke(self, context, event):
        bpy.ops.ed.undo_push(message="Delete Pattern")
        get_collection_by_idx(self.collectionIdx).remove_pattern()

        return {'FINISHED'}


class NeoTileAddPatternRect(bpy.types.Operator):
    bl_idname = "neo.uvset_add_pattern_rect"
    bl_label = "Add Pattern Rect"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()

    def invoke(self, context, event):
        collection =  get_collection_by_idx(self.collectionIdx)
        pattern = collection.get_active_pattern()
        pattern.add_rect()

        items = pattern.items.items()
        bpy.ops.view3d.nuv_set_pattern_rect_selector(
            "INVOKE_DEFAULT",
            collectionIdx=self.collectionIdx,
            patternRectIdx=len(items) - 1)

        return {'FINISHED'}


class NeoTileSetPatternRect(bpy.types.Operator):
    bl_idname = "neo.uvset_set_pattern_rect"
    bl_label = "Set Pattern Rect"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()
    patternRectIdx: bpy.props.IntProperty()
    rectIdx: bpy.props.IntProperty()

    def invoke(self, context, event):
        collection = get_collection_by_idx(self.collectionIdx)
        pattern = collection.get_active_pattern()

        pattern.set_rect(self.collectionIdx, self.patternRectIdx, self.rectIdx)
        return {'FINISHED'}


class NeoTileDeletePatternRect(bpy.types.Operator):
    bl_idname = "neo.uvset_delete_pattern_rect"
    bl_label = "Delete Pattern Rect"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()
    patternRectIdx: bpy.props.IntProperty()

    def invoke(self, context, event):
        collection = get_collection_by_idx(self.collectionIdx)
        pattern = collection.get_active_pattern()

        pattern.delete_rect(self.patternRectIdx)

        return {'FINISHED'}


class NeoTileDeleteCollection(bpy.types.Operator):
    bl_idname = "neo.uvset_delete"
    bl_label = "Delete"
    bl_description = ""

    collectionIdx: bpy.props.IntProperty()

    def invoke(self, context, event):

        bpy.ops.ed.undo_push(message="Delete NeoTileMap")
        get_collections().remove(self.collectionIdx)

        return {'FINISHED'}

# endregion

# region Import Classes


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
    def add_image(file_path, name):
        """Adds an image to the blend file, replacing it if it already exists.

        Args:
            file_path (str): The filepath of the image to add.
            name (str): The name to give the image in the blend file
        """

        # delete image if it already exists
        for i in bpy.data.images:
            if i.name == name:
                i.filepath = file_path
                i.reload()
                i.pack()
                i.use_fake_user = True

                return

        image = bpy.data.images.load(file_path)
        image.name = name
        image.reload()
        image.pack()
        image.use_fake_user = True

    @staticmethod
    def add_collection(n, file_path):
        """Adds or discovers a new uv tile set collection to the blender scene.

        Args:
            n (str): The name to give the collection.
            file_path (str): THe path to the file that the collection was added from.

        Returns:
            NeoTileRectCollection: The collection that was created or discovered.
        """

        collection_list = bpy.context.scene.nuv_uvSets

        for i in range(0, len(collection_list)):
            collection = collection_list[i]
            if collection.name == n:
                collection.relative_path = file_path
                return collection

        new_set = bpy.context.scene.nuv_uvSets.add()
        new_set.name = n
        new_set.relative_path = file_path

        return new_set

    @staticmethod
    def clear_collection(n):
        """Clears all items from the collection with the given name.

        Args:
            n (str): The name of the collection to clear items from.
        """
        selection_list = bpy.context.scene.nuv_uvSets

        for i in range(0, len(selection_list)):
            collection = selection_list[i]
            if collection.name == n:
                collection.clear()

    @staticmethod
    def rect_verts_compare(a, verts):
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
    def add_rect_to_collection(verts, img_name, c):
        """Adds a rect to a given collection

        Args:
            verts (array): The array of vertices that make up the rect.
            img_name (str): The name of the image to assign as the rect preview.
            c (NeoTileRectCollection): The collection to add the rect to.
        """

        for t in c.items:
            if ImportRectData.rect_verts_compare(t, verts):
                ImportRectData.setup_rect(verts, img_name, t)
                return

        new_rect = c.items.add()
        ImportRectData.setup_rect(verts, img_name, new_rect)

    @staticmethod
    def setup_rect(verts, img_name, t):
        """Configures a rect.

        Args:
            verts (array): The array of vertices to use in the rect.
            img_name (str): The name of the image to use as the rects preview icon.
            t (NeoTileRect): The tile rect to configure.
        """

        t.previewName = img_name
        t.topLeftX = verts[0][0]
        t.topLeftY = verts[0][1]

        t.topRightX = verts[1][0]
        t.topRightY = verts[1][1]

        t.bottomRightX = verts[2][0]
        t.bottomRightY = verts[2][1]

        t.bottomLeftX = verts[3][0]
        t.bottomLeftY = verts[3][1]

    @staticmethod
    def to_verts(top_left_x, top_left_y,
                 top_right_x, top_right_y,
                 bottom_right_x, bottom_right_y,
                 bottom_left_x, bottom_left_y):
        """Takes a series of split vertex elements and joins them into a multidimensional array for convient access
        """

        return [[top_left_x, top_left_y],
                [top_right_x, top_right_y],
                [bottom_right_x, bottom_right_y],
                [bottom_left_x, bottom_left_y]]

    @staticmethod
    def import_file(filepath):
        try:
            relpath = os.path.relpath(filepath)
        except:
            relpath = filepath

        with open(filepath, "rb") as f:
            byte_order = 'little'

            file_len = os.path.getsize(filepath)
            loadedcontent = []

            # read header
            id_len = int.from_bytes(f.read(1), byteorder=byte_order, signed=False)
            id_name = f.read(id_len).decode("utf-8")

            if id_name != "NEOPROJ":
                return {'CANCELLED'}

            # version
            version = int.from_bytes(f.read(4), byteorder=byte_order, signed=False)

            # load data
            while f.tell() < file_len:
                new_content = ProjectFileContent(f)
                loadedcontent.append(new_content)

                curr_pos = f.tell()
                f.seek(curr_pos + new_content.dataLen)

            # process data
            for c in loadedcontent:
                f.seek(c.dataAddress)

                if c.name == "atlas":
                    # not needed for blender loading
                    tile_width = int.from_bytes(f.read(4), byteorder=byte_order, signed=True)
                    tile_height = int.from_bytes(f.read(4), byteorder=byte_order, signed=True)

                    png_len = int.from_bytes(f.read(4), byteorder=byte_order, signed=True)
                    png_bytes = f.read(png_len)

                    # save atlas to a temp location and then reload it
                    img_name = Path(filepath).stem
                    img_path = os.path.join(os.path.dirname(filepath), img_name + "_atlas.png")

                    with open(img_path, mode="wb") as atlasF:
                        atlasF.write(png_bytes)

                    ImportRectData.add_image(img_path, "Atlas_" + img_name)

                    # we're done with the file, remove it
                    if os.path.exists(img_path): os.remove(img_path)
                elif c.name == "uvs":
                    rect_count = int.from_bytes(f.read(4), byteorder=byte_order, signed=True)

                    # clear the collection if it already exists
                    img_name = Path(filepath).stem
                    ImportRectData.clear_collection(img_name)

                    for i in range(0, rect_count):
                        # uv vertex positions
                        top_left_x = struct.unpack('f', f.read(4))[0]
                        top_left_y = struct.unpack('f', f.read(4))[0]

                        top_right_x = struct.unpack('f', f.read(4))[0]
                        top_right_y = struct.unpack('f', f.read(4))[0]

                        bottom_right_x = struct.unpack('f', f.read(4))[0]
                        bottom_right_y = struct.unpack('f', f.read(4))[0]

                        bottom_left_x = struct.unpack('f', f.read(4))[0]
                        bottom_left_y = struct.unpack('f', f.read(4))[0]

                        # preview texture data
                        png_len = int.from_bytes(f.read(4), byteorder=byte_order, signed=True)
                        png_bytes = f.read(png_len)

                        img_path = os.path.join(os.path.dirname(filepath), img_name + "_preview.png")

                        with open(img_path, mode="wb") as previewF:
                            previewF.write(png_bytes)

                        preview_name = ".Atlas_" + img_name + "_Preview" + str(i)
                        ImportRectData.add_image(img_path, preview_name)

                        # we're done with the file, remove it
                        if os.path.exists(img_path): os.remove(img_path)

                        # create collection item
                        verts = ImportRectData.to_verts(top_left_x, top_left_y,
                                                        top_right_x, top_right_y,
                                                        bottom_right_x, bottom_right_y,
                                                        bottom_left_x, bottom_left_y)

                        collection = ImportRectData.add_collection(img_name, relpath)
                        ImportRectData.add_rect_to_collection(verts, preview_name, collection)

                        collection.update_pattern_indicies()
        return {'FINISHED'}

    def execute(self, context):
        report = self.import_file(self.properties.filepath)
        for r in report:
            if r == "CANCELLED":
                self.report({"ERROR"}, "Not a valid tile map project file.")

        return report


class ProjectFileContent:
    """Contains data read from a neognosisi project file.
    """

    def __init__(self, f):
        name_len = int.from_bytes(f.read(1), byteorder='little', signed=False)
        self.name = f.read(name_len).decode('utf-8')
        self.dataLen = int.from_bytes(f.read(8), byteorder='little', signed=True)
        self.dataAddress = f.tell()

# endregion

# region Blender


classes = (
    ImportRectData,
    NeoTileRect,
    NeoTilePatternEntry,
    NeoTileRectPattern,
    NeoTileRectCollection,
    NeoTileDeleteCollection,
    NeoTileAddPattern,
    NeoTileDeletePattern,
    NeoTileAddPatternRect,
    NeoTileSetPatternRect,
    NeoTileDeletePatternRect,
)


def menu_import(self, context):
    self.layout.operator(ImportRectData.bl_idname, text="Neognosis Tile Set (.tmprj)")


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    setup_props()


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    desetup_props()


def setup_props():
    bpy.types.Scene.nuv_uvSets = bpy.props.CollectionProperty(type=NeoTileRectCollection)


def desetup_props():
    pass
# endregion
