import requests
import platform
import threading
import time
import os

# Config
SERVER_URL = "http://127.0.0.1:5000"
HEARTBEAT_INTERVAL = 30  # seconds
IDLE_TIMEOUT = 600  # seconds (10 minutes)

class DCCClient:
    """
    A client to communicate with the time tracking server from a DCC application.
    Now includes idle detection.
    """
    def __init__(self, dcc_name):
        self.dcc_name = dcc_name
        self.session_id = None
        self.user_info = None
        self.machine = platform.node()
        
        # Threading and state management
        self.heartbeat_thread = None
        self.stop_event = threading.Event()
        self.is_paused = False
        self.last_active_time = time.time()

        print(f"DCCClient initialized for {dcc_name} on {self.machine}")

    def get_tasks(self):
        """Fetches the list of available tasks from the server."""
        try:
            response = requests.get(f"{SERVER_URL}/api/tasks", timeout=5)
            if response.status_code == 200:
                return response.json().get("tasks", [])
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tasks: {e}")
            return []

    def login(self, username, password):
        """Authenticates the user with the server."""
        payload = {"username": username, "password": password}
        try:
            response = requests.post(f"{SERVER_URL}/api/login", json=payload, timeout=5)
            if response.status_code == 200:
                self.user_info = response.json().get("user")
                print(f"Login successful for user: {self.user_info['username']}")
                return True
            print(f"Login failed: {response.json().get('message')}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Login error: Could not connect to the server. {e}")
            return False

    def start_session(self, project_name, scene_name, task_id):
        """Starts a new tracking session."""
        if not self.user_info:
            print("Cannot start session: User not logged in.")
            return

        payload = {
            "user_id": self.user_info['id'], "task_id": task_id,
            "machine": self.machine, "dcc_name": self.dcc_name,
            "project_name": project_name, "scene_name": scene_name
        }
        try:
            response = requests.post(f"{SERVER_URL}/api/session/start", json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                self.session_id = data.get("session_id")
                print(f"Time tracker session started. ID: {self.session_id}")
                self._start_background_thread()
        except requests.exceptions.RequestException as e:
            print(f"Error starting session: {e}")

    def stop_session(self):
        """Stops the current tracking session."""
        if self.session_id is None:
            return
        
        self.stop_event.set() # Signal the background thread to stop
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)

        try:
            requests.post(f"{SERVER_URL}/api/session/stop", json={"session_id": self.session_id}, timeout=5)
            print(f"Time tracker session stopped. ID: {self.session_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error stopping session: {e}")
        finally:
            self.session_id = None
            self.is_paused = False

    def send_heartbeat(self):
        """Sends a heartbeat to the server and marks the user as active."""
        if self.session_id is None or self.stop_event.is_set():
            return
        
        # If paused, resume the session first
        if self.is_paused:
            self._resume_session()

        self.last_active_time = time.time()
        try:
            requests.post(f"{SERVER_URL}/api/session/heartbeat", json={"session_id": self.session_id}, timeout=3)
            # print(f"Sent heartbeat for session {self.session_id}") # Can be noisy
        except requests.exceptions.RequestException:
            print("Heartbeat failed. Server unreachable.")
    
    def _pause_session(self):
        """Internal method to pause the session."""
        if self.session_id and not self.is_paused:
            print("User idle. Pausing session...")
            self.is_paused = True
            try:
                requests.post(f"{SERVER_URL}/api/session/pause", json={"session_id": self.session_id}, timeout=5)
            except requests.exceptions.RequestException as e:
                print(f"Error pausing session: {e}")

    def _resume_session(self):
        """Internal method to resume the session."""
        if self.session_id and self.is_paused:
            print("User active. Resuming session...")
            self.is_paused = False
            try:
                requests.post(f"{SERVER_URL}/api/session/resume", json={"session_id": self.session_id}, timeout=5)
            except requests.exceptions.RequestException as e:
                print(f"Error resuming session: {e}")

    def _background_worker(self):
        """The main loop for the background thread."""
        while not self.stop_event.is_set():
            if self.session_id:
                # Check for idleness
                if not self.is_paused and (time.time() - self.last_active_time > IDLE_TIMEOUT):
                    self._pause_session()
                
                # The heartbeat is sent manually by the DCC app,
                # this thread is just for checking idleness.
            
            time.sleep(HEARTBEAT_INTERVAL)

    def _start_background_thread(self):
        """Starts the background thread for heartbeats and idle checks."""
        if self.heartbeat_thread is None or not self.heartbeat_thread.is_alive():
            self.stop_event.clear()
            self.last_active_time = time.time()
            self.is_paused = False
            self.heartbeat_thread = threading.Thread(target=self._background_worker, daemon=True)
            self.heartbeat_thread.start()
            print("Idle detection thread started.")
