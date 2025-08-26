import maya.cmds as cmds
import maya.utils
import dcc_client
import os
import atexit
import time

# Global Variables
tracker_instance = None
task_list = []
# A list to hold all our activity-based scriptJob IDs
activity_job_ids = []

def login_and_start_session():
    """Handles the login process and starts the tracking session."""
    global tracker_instance

    if tracker_instance and tracker_instance.user_info:
        create_task_selection_window()
        return

    tracker_instance = dcc_client.DCCClient("maya")
    
    window_name = "vfxTrackerLoginWindow"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    cmds.window(window_name, title="VFX Tracker Login", widthHeight=(300, 190))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 5))
    cmds.text(label="Please log in to start tracking.", align='center')
    cmds.separator(height=10)
    cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 80), (2, 200)])
    cmds.text(label="Username:")
    username_field = cmds.textField()
    cmds.text(label="Password:")
    password_field = cmds.textField()
    cmds.setParent('..')
    cmds.text(label="(Password will be visible)", align='center', font='smallObliqueLabelFont')
    cmds.separator(height=5, style='in')
    cmds.button("loginButton", label='Login', command=lambda *args: on_login_button_press(username_field, password_field), height=30)
    cmds.setParent('..')
    cmds.showWindow(window_name)

def on_login_button_press(username_field, password_field):
    """Callback for the login button."""
    global tracker_instance
    username = cmds.textField(username_field, query=True, text=True)
    password = cmds.textField(password_field, query=True, text=True)
    
    if not username or not password:
        cmds.warning("Username and password cannot be empty.")
        return

    if tracker_instance.login(username, password):
        cmds.deleteUI("vfxTrackerLoginWindow")
        create_task_selection_window()
    else:
        cmds.warning("Login failed. Please check your credentials.")

def create_task_selection_window():
    """Creates a window for the user to select a task."""
    global task_list
    task_list = tracker_instance.get_tasks()

    window_name = "vfxTaskSelectionWindow"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    cmds.window(window_name, title="Select Task", widthHeight=(300, 100))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 5))
    cmds.text(label="Select a task to begin tracking:")
    task_menu = cmds.optionMenu("taskOptionMenu")
    for task in task_list:
        cmds.menuItem(label=task['task_name'])

    def on_start_tracking_press(*args):
        selected_task_name = cmds.optionMenu(task_menu, query=True, value=True)
        start_new_session(selected_task_name)
        cmds.deleteUI(window_name)

    cmds.button(label="Start Tracking", command=on_start_tracking_press, height=30)
    cmds.setParent('..')
    cmds.showWindow(window_name)

def start_new_session(selected_task_name):
    """Starts a new session and the heartbeat timer."""
    global tracker_instance, task_list

    if not tracker_instance or not tracker_instance.user_info:
        return
        
    if tracker_instance.session_id:
        tracker_instance.stop_session()

    kill_activity_jobs() # Kill any existing jobs

    selected_task_id = None
    for task in task_list:
        if task['task_name'] == selected_task_name:
            selected_task_id = task['id']
            break

    workspace = cmds.workspace(q=True, rootDirectory=True)
    project_name = os.path.basename(workspace.strip('/')) if workspace else "Maya Project"
    scene_path = cmds.file(q=True, sceneName=True)
    scene_name = os.path.basename(scene_path) if scene_path else "Unsaved Scene"
    
    tracker_instance.start_session(project_name, scene_name, selected_task_id)
    
    # Create scriptJobs that are tied to actual user activity.
    setup_activity_jobs()
    
    create_tracker_control_window(selected_task_name)

def setup_activity_jobs():
    """Creates scriptJobs that fire on user interaction to send heartbeats."""
    global activity_job_ids
    heartbeat_command = "import maya_tracker_integration; maya_tracker_integration.tracker_instance.send_heartbeat()"
    
    # List of events that indicate user activity
    activity_events = ["timeChanged", "SelectionChanged", "DragRelease", "Undo", "Redo"]
    
    for event in activity_events:
        job_id = cmds.scriptJob(event=[event, heartbeat_command], protected=True)
        activity_job_ids.append(job_id)
    print(f"Activity scriptJobs created: {activity_job_ids}")

def kill_activity_jobs():
    """Kills all active activity-monitoring scriptJobs."""
    global activity_job_ids
    for job_id in activity_job_ids:
        if cmds.scriptJob(exists=job_id):
            cmds.scriptJob(kill=job_id, force=True)
    activity_job_ids = []
    print("Activity scriptJobs killed.")

def create_tracker_control_window(current_task):
    """Creates the main control UI for the tracker."""
    window_name = "vfxTrackerControlWindow"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)
        
    cmds.window(window_name, title="VFX Tracker", widthHeight=(250, 100))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
    cmds.text(label="Currently Tracking:", font="boldLabelFont")
    cmds.text(label=current_task)
    cmds.separator(height=10, style='in')
    cmds.button(label="Change Task", command=lambda *args: change_task())
    cmds.button(label="Stop Tracking", command=lambda *args: stop_tracking_and_close())
    cmds.showWindow(window_name)

def change_task(*args):
    """Stops the current session and re-opens the task selection window."""
    if tracker_instance:
        tracker_instance.stop_session()
    kill_activity_jobs()
    create_task_selection_window()

def stop_tracking_and_close(*args):
    """Stops the session and cleans up UI and jobs."""
    global tracker_instance
    if tracker_instance:
        tracker_instance.stop_session()
        tracker_instance = None
    
    kill_activity_jobs()
    
    if cmds.window("vfxTrackerControlWindow", exists=True):
        cmds.deleteUI("vfxTrackerControlWindow")
    cmds.warning("Tracking has been stopped.")

def on_maya_exit(*args):
    """Fallback for when Maya is about to exit."""
    global tracker_instance
    if tracker_instance:
        tracker_instance.stop_session()

def initialize_tracker():
    """Sets up the necessary callbacks in Maya."""
    scene_opened_command = "import maya_tracker_integration; maya_tracker_integration.login_and_start_session()"
    maya_exit_command = "import maya_tracker_integration; maya_tracker_integration.on_maya_exit()"
    
    cmds.scriptJob(event=["SceneOpened", scene_opened_command], protected=True)
    cmds.scriptJob(event=["NewSceneOpened", scene_opened_command], protected=True)
    
    try:
        cmds.scriptJob(event=["MayaExiting", maya_exit_command], protected=True)
    except:
        atexit.register(on_maya_exit)

    print("Time Tracker callbacks installed.")

# Main execution
try:
    maya.utils.executeInMainThreadWithResult(initialize_tracker)
    print("VFX Time Tracker integration loaded successfully.")
except Exception as e:
    print(f"Failed to initialize VFX Time Tracker: {e}")
