bl_info = {
    "name": "VFX Time Tracker",
    "author": "Your Name",
    "version": (1, 7, 0), # Activity-based idle detection
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > VFX Time Tracker",
    "description": "Log in and track time for VFX projects.",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import sys
import os
import atexit
from bpy.app.handlers import persistent
from bpy.props import StringProperty, PointerProperty, EnumProperty
from bpy.types import PropertyGroup, Scene

# Add the addon's directory to the python path
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

# Import the dcc_client module 
import dcc_client

# Global variables 
tracker_instance = None
task_list = []

# UI and Properties Classes

def get_tasks_for_enum(self, context):
    """Callback function for the EnumProperty to display tasks."""
    global task_list
    if not task_list:
        return [("0", "No Tasks Found", "Log in to fetch tasks")]
    return [(str(task['id']), task['task_name'], "") for task in task_list]

class TrackerProperties(PropertyGroup):
    """Stores the add-on's properties for the UI."""
    username: StringProperty(name="Username", default="") # type: ignore
    password: StringProperty(name="Password", default="", subtype='PASSWORD') # type: ignore
    login_status: StringProperty(name="Status", default="Logged Out") # type: ignore
    task_enum: EnumProperty(name="Task", items=get_tasks_for_enum) # type: ignore

class LoginOperator(bpy.types.Operator):
    """Operator to handle the login button press."""
    bl_idname = "vfx_tracker.login"
    bl_label = "Login"

    def execute(self, context):
        global tracker_instance, task_list
        props = context.scene.vfx_tracker_props
        
        if not props.username or not props.password:
            self.report({'WARNING'}, "Username and password cannot be empty.")
            return {'CANCELLED'}

        tracker_instance = dcc_client.DCCClient("blender")
        if tracker_instance.login(props.username, props.password):
            props.login_status = f"Logged in as: {props.username}"
            task_list = tracker_instance.get_tasks()
            self.report({'INFO'}, "Login successful! Select a task to start.")
        else:
            props.login_status = "Login Failed"
            self.report({'ERROR'}, "Login failed.")
        
        return {'FINISHED'}

class StartTrackingOperator(bpy.types.Operator):
    """Operator to start a tracking session."""
    bl_idname = "vfx_tracker.start_tracking"
    bl_label = "Start Tracking"

    def execute(self, context):
        start_new_session()
        return {'FINISHED'}

class StopTrackingOperator(bpy.types.Operator):
    """Operator to stop a tracking session and log out."""
    bl_idname = "vfx_tracker.stop_tracking"
    bl_label = "Stop Tracking"

    def execute(self, context):
        global tracker_instance
        props = context.scene.vfx_tracker_props
        if tracker_instance:
            tracker_instance.stop_session()
            tracker_instance = None
            props.login_status = "Logged Out"
        kill_activity_handlers()
        self.report({'INFO'}, "Tracking stopped and logged out.")
        return {'FINISHED'}

class VFXTrackerPanel(bpy.types.Panel):
    """Creates the main UI Panel in the 3D View's Sidebar."""
    bl_label = "VFX Time Tracker"
    bl_idname = "VIEW3D_PT_vfx_tracker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VFX Time Tracker'

    def draw(self, context):
        layout = self.layout
        props = context.scene.vfx_tracker_props
        layout.label(text=props.login_status)
        layout.separator()
        
        is_logged_in = tracker_instance and tracker_instance.user_info
        is_tracking = is_logged_in and tracker_instance.session_id

        if not is_logged_in:
            layout.prop(props, "username")
            layout.prop(props, "password")
            layout.operator("vfx_tracker.login")
        else:
            layout.prop(props, "task_enum")
            if not is_tracking:
                layout.operator("vfx_tracker.start_tracking")
            else:
                layout.label(text="Session is active.")
                layout.operator("vfx_tracker.start_tracking", text="Change Task")
                layout.operator("vfx_tracker.stop_tracking")

# Heartbeat and Session Management

def send_heartbeat(dummy):
    """Function called by activity handlers to send a heartbeat."""
    if tracker_instance and tracker_instance.session_id:
        tracker_instance.send_heartbeat()

def start_new_session():
    """Starts a new session based on the UI selection."""
    global tracker_instance

    if not tracker_instance or not tracker_instance.user_info:
        return

    if tracker_instance.session_id:
        tracker_instance.stop_session()

    kill_activity_handlers() # Ensure old handlers are cleared

    props = bpy.context.scene.vfx_tracker_props
    selected_task_id = int(props.task_enum) if props.task_enum.isdigit() and int(props.task_enum) > 0 else None
    filepath = bpy.data.filepath
    project_name = os.path.basename(os.path.dirname(filepath)) if filepath else "blender_project"
    scene_name = os.path.basename(filepath) if filepath else "Unsaved Scene"

    tracker_instance.start_session(project_name, scene_name, selected_task_id)
    setup_activity_handlers() # Start sending heartbeats for the new session

# Activity Handlers 
_activity_handlers = []

def setup_activity_handlers():
    """
    Registers handlers for events that signify user activity.
    These will call the send_heartbeat function.
    """
    global _activity_handlers
    kill_activity_handlers() # Make sure we start fresh

    # A list of handler lists in bpy.app.handlers
    handler_owners = [
        bpy.app.handlers.render_post,
        bpy.app.handlers.save_post,
        bpy.app.handlers.depsgraph_update_post,
        bpy.app.handlers.frame_change_post
    ]

    for handler_list in handler_owners:
        handler_list.append(send_heartbeat)
        _activity_handlers.append((handler_list, send_heartbeat))
    
    print(f"Activity handlers registered.")

def kill_activity_handlers():
    """Removes all registered activity handlers."""
    global _activity_handlers
    for handler_list, func in _activity_handlers:
        if func in handler_list:
            handler_list.remove(func)
    _activity_handlers = []
    print("Activity handlers killed.")


@persistent
def on_blender_exit():
    """Fallback for when Blender is about to close."""
    global tracker_instance
    if tracker_instance:
        tracker_instance.stop_session()

# Registration

classes = (
    TrackerProperties,
    LoginOperator,
    StartTrackingOperator,
    StopTrackingOperator,
    VFXTrackerPanel,
)

def register():
    """Registers the add-on, its UI, and callbacks."""
    for cls in classes:
        bpy.utils.register_class(cls)
    Scene.vfx_tracker_props = PointerProperty(type=TrackerProperties)
    atexit.register(on_blender_exit)
    print("VFX Time Tracker: Add-on registered successfully.")

def unregister():
    """Unregisters the add-on and removes callbacks."""
    kill_activity_handlers()
    try:
        atexit.unregister(on_blender_exit)
    except Exception:
        pass
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del Scene.vfx_tracker_props
    print("VFX Time Tracker: Add-on unregistered.")
