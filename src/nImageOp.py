# region Imports

import bpy

# blender 4.4 must have additional params for __init__
is_blender_44_or_greater = bpy.app.version[0] > 3 and bpy.app.version[1] > 3

# endregion

# region Operators


# noinspection PyAttributeOutsideInit
class NeoImageOperator(bpy.types.Operator):
    """Base class for all neognosis image editor tools."""

    if is_blender_44_or_greater:
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.init()

    else:
        def __init__(self):
            super().__init__()
            self.init()

    def init(self):
        # mouse data
        self.mouse_held = [False, False, False]
        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.mouse_prev_x = 0.0
        self.mouse_prev_y = 0.0
        self.mouse_region_x = 0.0
        self.mouse_region_y = 0.0
        self.mouse_delta_x = 0.0
        self.mouse_delta_y = 0.0

        # editor data
        self.zoom = 0.5
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.image = None

        # grid data
        self.grid_x = 16
        self.grid_y = 16

        # reports
        self.report_finished = {'FINISHED'}
        self.report_cancelled = {'CANCELLED'}
        self.report_running = {'RUNNING_MODAL'}

    def modal(self, context, event):

        context.area.tag_redraw()

        # update mouse data
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y
        self.mouse_prev_x = event.mouse_prev_x
        self.mouse_prev_y = event.mouse_prev_y
        self.mouse_region_x = event.mouse_region_x
        self.mouse_region_y = event.mouse_region_y
        self.mouse_delta_x = self.mouse_x - self.mouse_prev_x
        self.mouse_delta_y = self.mouse_y - self.mouse_prev_y

        # mouse wheel events
        if event.type == 'WHEELUPMOUSE':
            self.on_scroll_up(context)

        if event.type == 'WHEELDOWNMOUSE':
            self.on_scroll_down(context)

        # mouse click events
        if event.type == 'LEFTMOUSE':
            self.__handle_mouse_event(context, event, 0)

        if event.type == 'RIGHTMOUSE':
            self.__handle_mouse_event(context, event, 1)

        if event.type == 'MIDDLEMOUSE':
            self.__handle_mouse_event(context, event, 2)

        close = self.on_update(context, event)

        if close:
            self.on_close(context, event)
            return self.report_finished
        else:
            return self.report_running

    def on_update(self, context, event):
        pass

    def invoke(self, context, event):
        self.on_open(context, event)
        context.window_manager.modal_handler_add(self)
        return self.report_running

    def on_open(self, context, event):
        """Called when the image editor is opened."""

    def on_close(self, context, event):
        """Called when the image editor is closed."""

    def __handle_mouse_event(self, context, event, btn_idx):
        """Handles a mouse input event and updates the class

        Args:
            context (context): The context provided by Blender
            event (bool): The event provided by Blender
            btn_idx (int): The index of the button that was pressed
        """
        if event.value == 'PRESS':
            self.on_mouse_down(context, btn_idx)
            self.mouse_held[btn_idx] = True

        if event.value == 'RELEASE':
            self.on_mouse_up(context, btn_idx)
            self.mouse_held[btn_idx] = False

        if self.mouse_held[btn_idx]:
            self.on_mouse_held(context, btn_idx)

    def __report_should_return(self, report):
        return report in (self.report_finished, self.report_cancelled)

    def on_mouse_down(self, context, btn_idx):
        """Called when a mouse button is pressed down.

        Args:
            context (context): The context provided by Blender
            btn_idx (int): The index of the button that was pressed
        """

    def on_mouse_up(self, context, btn_idx):
        """Called when a mouse button is released.

        Args:
            context (context): The context provided by Blender
            btn_idx (int): The index of the button that was released
        """

    def on_mouse_held(self, context, btn_idx):
        """Called when a mouse button is held

        Args:
            context (context): The context provided by Blender
            btn_idx (int): The index of the button that is held
        """

    def on_scroll_up(self, context):
        """Called when the mouse is scrolled up.

        Args:
            context (context): The context provided by Blender
        """

    def on_scroll_down(self, context):
        """Called when the mouse is scrolled down.

        Args:
            context (context): The context provided by Blender
        """
# endregion
