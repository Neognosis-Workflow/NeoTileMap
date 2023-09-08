pass

import bpy
import math
from bpy.props import *
import nUtil
from . import nMath

def draw_seteditor_px(self, image, context):
    #blf.position(0, 15, 30, 0)
    #blf.size(0, 20, 72)
    #blf.draw(0, str(self.zoom))

    # calculate image size
    imgRes = image.size
    imgAspect = imgRes[0] / imgRes[1]

    quadWidth = (imgRes[1] * self.zoom) * imgAspect
    quadHeight = imgRes[0] * self.zoom

    # calculate position of image center
    areaWidth = context.area.width
    areaHeight = context.area.height

    centerX = (areaWidth / 2)
    centerY = (areaHeight / 2)

    # calculate image bounds
    bottom_left = ((centerX - quadWidth / 2) + self.offsetX, (centerY - quadHeight / 2) + self.offsetY)
    bottom_right = ((centerX + quadWidth / 2) + self.offsetX, (centerY - quadHeight / 2) + self.offsetY)
    top_left = ((centerX - quadWidth / 2) + self.offsetX, (centerY + quadHeight / 2) + self.offsetY)
    top_right = ((centerX + quadWidth / 2) + self.offsetX, (centerY + quadHeight / 2) + self.offsetY)

    # draw mesh
    verts = (
        bottom_left,
        bottom_right,
        top_left,
        top_right
    )

    texCoord = (
        (0, 0), (1, 0), (0, 1), (1, 1)
    )

    indices = (
        (0, 1, 2), (2, 1, 3)
    )
    
    nUtil.draw_image(image, verts, texCoord, indices)

    # draw grid
    gridStepsX = self.gridX
    gridStepsY = self.gridY

    xItr = int(imgRes[0] / gridStepsX)
    yItr = int(imgRes[1] / gridStepsY)

    stepSizeX = gridStepsX / imgRes[0]
    stepSizeY = gridStepsY / imgRes[1]

    lineColor = (1.0, 1.0, 1.0, 0.1)
    highlightColor = (0.0, 1.0, 0.0, 1.0)
    boundsColor = (0.0, 0.5, 1.0, 1.0)
    for x in range(0, xItr):
        xOffset = (x / xItr) * quadWidth

        posUpper = [top_left[0] + xOffset, top_left[1]]
        posLower = [bottom_left[0] + xOffset, bottom_left[1]]
        nUtil.line_draw(posUpper, posLower, lineColor)
        
        # draw cap line
        if x == xItr - 1:
            step = (1 / xItr) * quadWidth
            posUpper[0] += step
            posLower[0] += step
            nUtil.line_draw(posUpper, posLower, lineColor)

    for y in range(0, yItr):
        yOffset = (y / yItr) * quadHeight

        posLeft = [top_left[0], top_left[1] - yOffset]
        posRight = [top_right[0], top_right[1] - yOffset]
        nUtil.line_draw(posLeft, posRight, lineColor)

        if y == yItr - 1:
            step = (1 / yItr) * quadHeight
            posLeft[1] -= step
            posRight[1] -= step
            nUtil.line_draw(posLeft, posRight, lineColor)

    # handle mouse
    mouseX = nMath.inverse_lerp(bottom_left[0], bottom_right[0], self.mouseRegionX, False)
    mouseY = nMath.inverse_lerp(top_left[1], bottom_left[1],  self.mouseRegionY, False)

    if mouseX >= 0 and mouseX <= 1 and mouseY >= 0 and mouseY <= 1:
        gridX = math.floor((mouseX * imgRes[0]) / self.gridX)
        gridY = math.floor((mouseY * imgRes[1]) / self.gridY)

        if self.leftClickDown:
            self.gridA = [gridX, gridY]
            self.gridB = [-1, -1]

        if self.leftClickHeld:
            self.gridB = [gridX, gridY]

            # draw selection
            if self.gridA[0] != -1 and self.gridB[0] != -1:
                gridAVerts = get_grid_verts(self.gridA , xItr, yItr, quadWidth, quadHeight, bottom_left, bottom_right, top_left, top_right)
                gridBVerts = get_grid_verts(self.gridB, xItr, yItr, quadWidth, quadHeight, bottom_left, bottom_right, top_left, top_right)

                draw_highlightSelection(self.gridA, self.gridB, gridAVerts, gridBVerts, boundsColor)
            elif self.gridA[0] != -1:
                gridAVerts = get_grid_verts(self.gridA, xItr, yItr, quadWidth, quadHeight, bottom_left, bottom_right, top_left, top_right)
                draw_highlightFrame(gridAVerts, highlightColor)
        else:
            highlight = get_grid_verts([gridX, gridY], xItr, yItr, quadWidth, quadHeight, bottom_left, bottom_right, top_left, top_right)
            draw_highlightFrame(highlight, highlightColor)

        if self.leftClickUp:
            gridSorted = nUtil.grid_sort(self.gridA, self.gridB)
            self.gridA = gridSorted[0]
            self.gridB = gridSorted[1]

    else:
        if self.leftClickUp:
            self.gridA = [-1, -1]
            self.gridB = [-1, -1]

def draw_highlightFrame(gridVerts, color):
    nUtil.line_draw(gridVerts[0], gridVerts[1], color)
    nUtil.line_draw(gridVerts[1], gridVerts[2], color)
    nUtil.line_draw(gridVerts[2], gridVerts[3], color)
    nUtil.line_draw(gridVerts[3], gridVerts[0], color)

def draw_highlightSelection(a, b, aVerts, bVerts, color):
    if b[0] < a[0] or b[1] < a[1]:
        tr = [aVerts[1][0], bVerts[1][1]]
        bl = [bVerts[0][0], aVerts[3][1]]

        nUtil.line_draw(bVerts[0], tr, color)
        nUtil.line_draw(tr, aVerts[2], color)
        nUtil.line_draw(aVerts[2], bl, color)
        nUtil.line_draw(bl, bVerts[0], color)
    else:
        tr = [bVerts[1][0], aVerts[1][1]]
        bl = [aVerts[0][0], bVerts[3][1]]

        nUtil.line_draw(aVerts[0], tr, color)
        nUtil.line_draw(tr, bVerts[2], color)
        nUtil.line_draw(bVerts[2], bl, color)
        nUtil.line_draw(bl, aVerts[0], color)

def get_grid_from_corners(a, b):
    # get sorted grid corners
    sortedCorners = nUtil.grid_sort(a, b)
    a = sortedCorners[0]
    b = sortedCorners[1]

    grid = []
    for x in range(a[0], b[0]):
        for y in range(a[1], b[1]):
            grid.append([x, y])

    return grid

def get_grid_verts(gridPos, gridSizeX, gridSizeY, imgWidth, imgHeight, bottom_left, bottom_right, top_left, top_right):

    grid_verts = [0.0, 0.0, 0.0, 0.0]

    xOffset = (gridPos[0] / gridSizeX) * imgWidth
    yOffset = (gridPos[1] / gridSizeY) * imgHeight

    xOffsetNext = ((gridPos[0] + 1) / gridSizeX) * imgWidth
    yOffsetNext = ((gridPos[1] + 1) / gridSizeY) * imgHeight

    # top left
    grid_verts[0] = [
        top_left[0] + xOffset,
        top_left[1] - yOffset,
    ]

    # top right
    grid_verts[1] = [
        top_left[0] + xOffsetNext,
        top_left[1] - yOffset,
    ]

    # bottom right
    grid_verts[2] = [
        top_left[0] + xOffsetNext,
        top_left[1] - yOffsetNext,
    ]

    # bottom left
    grid_verts[3] = [
        top_left[0] + xOffset,
        top_left[1] - yOffsetNext,
    ]

    return grid_verts

class TileSetAreaEditor(bpy.types.Operator):
    bl_idname = "view3d.nuv_seteditor"
    bl_label = "Neognosis UV Tileset Editor"

    setIdx: IntProperty(
        name="Set Index"
    )

    def modal(self, context, event):
        self.leftClickDown = False
        self.leftClickUp = False
        self.mouseX = event.mouse_x
        self.mouseY = event.mouse_y
        self.mouseRegionX = event.mouse_region_x
        self.mouseRegionY = event.mouse_region_y

        context.area.tag_redraw()

        # zoom input
        if event.type == 'WHEELUPMOUSE':
            zoomAmt = 0.1
            self.zoom += zoomAmt

            x = self.offsetX - context.area.width / 2
            y = self.offsetY - context.area.height / 2

            self.offsetX += (self.offsetX * zoomAmt) / self.zoom
            self.offsetY += (self.offsetY * zoomAmt) / self.zoom


        if event.type == 'WHEELDOWNMOUSE':
            zoomAmt = 0.1
            self.zoom -= zoomAmt
            if (self.zoom < zoomAmt):
                self.zoom = zoomAmt

            x = self.offsetX - context.area.width / 2
            y = self.offsetY - context.area.height / 2

            self.offsetX -= (self.offsetX * zoomAmt) / self.zoom
            self.offsetY -= (self.offsetY * zoomAmt) / self.zoom

        # pan input
        if event.type == "MIDDLEMOUSE":
            if event.value == 'PRESS':
                self.dragging = True
            elif event.value == "RELEASE":
                self.dragging = False

        if self.dragging:
            xDelta = event.mouse_x - event.mouse_prev_x
            yDelta = event.mouse_y - event.mouse_prev_y
        
            self.offsetX += xDelta
            self.offsetY += yDelta

        if event.type == "LEFTMOUSE":
            if event.value == 'PRESS':
                self.leftClickHeld = True
                self.leftClickDown = True
            elif event.value == 'RELEASE':
                self.leftClickUp = True
                self.leftClickHeld = False

        if event.type == 'RIGHTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            self.gridA = [-1, -1]
            self.gridB = [-1, -1]
            self.lastUvA = [0, 0]
            self.lastUvB = [0, 0]
            self.leftClickHeld = False
            self.gridX = 32
            self.gridY = 32
            self.zoom = 1.0
            self.dragging = 0.0
            self.offsetX = 0.0
            self.offsetY = 0.0


            tiles = bpy.context.scene.nuv_tileSets[self.setIdx]
            args = (self, tiles.getImage(), context)

            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_seteditor_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            return {'CANCELLED'}

class MAT_UL_NeognosisTextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        image = item.getImage()
        layout.label(text=image.name, icon_value=image.preview.icon_id)

class NeoGridPos(bpy.types.PropertyGroup):
    x: IntProperty(name="Grid Position X")
    y: IntProperty(name="Grid Position Y")

class NeoUv(bpy.types.PropertyGroup):
    x: FloatProperty()
    y: FloatProperty()

class NeoUvArea(bpy.types.PropertyGroup):
    name: StringProperty(name="Uv Name")

    grid_area: CollectionProperty(type=NeoGridPos)

    uvs_top_left: CollectionProperty(type=NeoUv)
    uvs_top_right: CollectionProperty(type=NeoUv)
    uvs_bottom_left: CollectionProperty(type=NeoUv)
    uvs_bottom_right: CollectionProperty(type=NeoUv)

class NeoImageSet(bpy.types.PropertyGroup):
    image: StringProperty(
        name="Image"
    )

    def getImage(self):
        imgIdx = bpy.data.images.find(self.image)
        if imgIdx >= 0:
            return bpy.data.images[imgIdx]
        
        return None

class NeoTileSet(bpy.types.PropertyGroup):
    name: StringProperty(
        name="Name",
        description="The name of this tile set.",
        default="New Tile Set"
    )

    expanded: BoolProperty(
        name="Expanded",
        default=True
    )

    imgExpanded: BoolProperty(
        name="Image Expanded"
    )

    uvAreaExpanded: BoolProperty(
        name="Uv Area Expanded"
    )

    imageIdx: IntProperty(
        name="Image Index"
    )

    areas: CollectionProperty(type=NeoUvArea)

    def getImage(self):
        maxIdx = len(bpy.data.images)
        if self.imageIdx > maxIdx - 1:
            return None

        return bpy.data.images[self.imageIdx]

class UTIL_OP_NeoRefreshTextures(bpy.types.Operator):
    bl_idname = "neo.uv_refreshtexturelist"
    bl_label = "NeoUV - Refresh Texture List"
    bl_description = "Refreshes the NeoUV tools texture list reference"

    def invoke(self, context, event):
        textures = bpy.context.scene.nuv_images
        textures.clear()

        for t in bpy.data.images:
            textures.add().image = t.name

        return {'FINISHED'}

class UTIL_OP_NeoCreateTileSet(bpy.types.Operator):
    bl_idname = "neo.uv_addset"
    bl_label = "Add Tile Set"
    bl_description = "Adds a new tile set."
    
    def invoke(self, context, event):
        setList = bpy.context.scene.nuv_tileSets
        setList.add()
        return {'FINISHED'}

class UTIL_OP_NeoDeleteTileSet(bpy.types.Operator):
    bl_idname = "neo.uv_delset"
    bl_label = "Remove Tile Set"
    bl_description = "Removes the tile set."

    index: IntProperty(name="index", default=0)

    def invoke(self, context, event):
        bpy.context.scene.nuv_tileSets.remove(self.index)
        return {'FINISHED'}

class PROP_OP_NeoPropsSetup(bpy.types.Operator):
    bl_idname = "neo.uv_props_setup"
    bl_label = "Setup Neognosis UV Data"

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        self.setup()
        return {'FINISHED'}
    
    @staticmethod
    def setup():
        bpy.types.Scene.nuv_tileSets = bpy.props.CollectionProperty(type=NeoTileSet)
        bpy.types.Scene.nuv_images = bpy.props.CollectionProperty(type=NeoImageSet)

class PROP_OP_NeoPropsDesetup(bpy.types.Operator):
    bl_idname = "neo.uv_props_desetup"
    bl_label = "Desetup Neognosis UV Data"

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        self.setup()
        return {'FINISHED'}
    
    @staticmethod
    def setup():
        del bpy.types.Scene.nuv_tileSets
        del bpy.types.Scene.nuv_images
    
classes = (
    UTIL_OP_NeoCreateTileSet,
    UTIL_OP_NeoDeleteTileSet,
    NeoGridPos,
    NeoUv,
    NeoUvArea,
    NeoTileSet,
    NeoImageSet,
    PROP_OP_NeoPropsSetup,
    PROP_OP_NeoPropsDesetup,
    UTIL_OP_NeoRefreshTextures,
    MAT_UL_NeognosisTextureList,
    TileSetAreaEditor,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

    PROP_OP_NeoPropsSetup.setup()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    
    PROP_OP_NeoPropsDesetup.setup()

def drawTileSetUi(layout, context):
    layout.operator("neo.uv_refreshtexturelist", text="Refresh Texture List")

    box = layout.box()
    box.label(text="Tile Sets")
    box.operator("neo.uv_addset")

    set_list = bpy.context.scene.nuv_tileSets
    for s in range(0, len(set_list)):
        tileSet = set_list[s]
        setBox = box.box()

        expandStr = "Hide " if tileSet.expanded else "Show "
        setBox.prop(tileSet, "expanded", icon="TRIA_DOWN" if tileSet.expanded else "TRIA_RIGHT", emboss=True, text=expandStr + tileSet.name)
        
        if tileSet.expanded:
            row = setBox.row()
            split = row.split(factor=0.4, align=True)
            split.operator("neo.uv_delset", text="Delete").index = s
            setBox.prop(tileSet, "name")

            texBox = setBox.box()
            expandStr = "Hide Texture Picker" if tileSet.imgExpanded else "Show Texture Picker"
            texBox.prop(tileSet, "imgExpanded", icon="TRIA_DOWN" if tileSet.imgExpanded else "TRIA_RIGHT", emboss=True, text=expandStr)

            if tileSet.imgExpanded:
                texBox.template_list("MAT_UL_NeognosisTextureList", "", bpy.context.scene, "nuv_images", tileSet, "imageIdx")

            row = setBox.row()
            row.operator("view3d.nuv_seteditor", text="Edit").setIdx = s

        