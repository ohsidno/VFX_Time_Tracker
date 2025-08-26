# userSetup.py
import maya.cmds as cmds

def initialize_time_tracker():
    """
    This function will be deferred until Maya's UI is fully loaded.
    """
    try:
        import maya_tracker_integration
        print("VFX Time Tracker integration loaded successfully.")
    except Exception as e:
        cmds.warning(f"Could not load VFX Time Tracker integration: {e}")

cmds.evalDeferred(initialize_time_tracker)
