# blender_tracker_integration.py
bl_info = {
    "name": "VFX Time Tracker Integration",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "System",
    "description": "Automatically tracks time and activity for the VFX Time Tracker.",
    "category": "System",
}

import bpy
import os
import sys
import threading
import time
from bpy.app.handlers import persistent

# Add dcc_client to Python's path 
# This is necessary because Blender's Python might not see it by default.
# Place dcc_client.py in the same folder as this script.
script_dir = os.path.dirname(os.path.realpath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

import dcc_client

# Globals for Blender Session
HEARTBEAT_TIMER = None
USER_ID = int(os.environ.get("STUDIO_USER_ID", 1))
APP_NAME = "blender"

def get_session_name_from_path(scene_path):
    """A robust function to extract context from a scene path."""
    try:
        clean_path = scene_path.replace("\\", "/")
        dir_parts = clean_path.split("/")[:-1]
        if "projects" in dir_parts:
            try:
                idx = dir_parts.index("projects")
                context = dir_parts[idx+1:idx+4]
                if context:
                    return " / ".join(context)
            except (ValueError, IndexError):
                pass
        if len(dir_parts) >= 3:
            return " / ".join(dir_parts[-3:])
        elif dir_parts:
            return " / ".join(dir_parts)
    except Exception as e:
        print(f"Error parsing session name: {e}")
    return "Unknown Session"

# Callback Functions
@persistent
def on_file_load_post(dummy):
    """Callback triggered after a .blend file is loaded."""
    print("Blender event: File Loaded")
    stop_heartbeat_timer()
    
    scene_path = bpy.data.filepath
    if not scene_path:
        dcc_client.stop_session()
        return
        
    session_name = get_session_name_from_path(scene_path)
    if dcc_client.start_session(USER_ID, APP_NAME, session_name, scene_path):
        start_heartbeat_timer()
        dcc_client.log_event("scene_open", scene_path)

@persistent
def on_blender_exit():
    """Callback triggered just before Blender exits."""
    print("Blender event: Exiting")
    dcc_client.log_event("blender_exit")
    stop_heartbeat_timer()
    dcc_client.stop_session()

# Heartbeat Timer 
def heartbeat_loop():
    """Sends a heartbeat to the server every 60 seconds."""
    while not HEARTBEAT_TIMER.stopped():
        dcc_client.send_heartbeat()
        for _ in range(60):
            if HEARTBEAT_TIMER.stopped():
                break
            time.sleep(1)

def start_heartbeat_timer():
    """Starts the heartbeat thread."""
    global HEARTBEAT_TIMER
    if HEARTBEAT_TIMER and HEARTBEAT_TIMER.is_alive():
        return
    HEARTBEAT_TIMER = threading.Thread(target=heartbeat_loop)
    HEARTBEAT_TIMER.stopped = threading.Event().is_set
    HEARTBEAT_TIMER.daemon = True
    HEARTBEAT_TIMER.start()
    print("Heartbeat timer started.")

def stop_heartbeat_timer():
    """Stops the heartbeat thread."""
    global HEARTBEAT_TIMER
    if HEARTBEAT_TIMER:
        HEARTBEAT_TIMER.stopped = lambda: True
        HEARTBEAT_TIMER = None
        print("Heartbeat timer stopped.")

# Add-on Registration 
def register():
    bpy.app.handlers.load_post.append(on_file_load_post)
    bpy.app.handlers.persistent_load.append(on_file_load_post) # For older Blender versions
    bpy.app.handlers.quit_post.append(on_blender_exit)
    print("VFX Time Tracker add-on registered.")

def unregister():
    bpy.app.handlers.load_post.remove(on_file_load_post)
    bpy.app.handlers.persistent_load.remove(on_file_load_post)
    bpy.app.handlers.quit_post.remove(on_blender_exit)
    print("VFX Time Tracker add-on unregistered.")

if __name__ == "__main__":
    register()
