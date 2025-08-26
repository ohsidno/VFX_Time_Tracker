# VFX Time Tracker

## 1. Project Overview

The VFX Time Tracker is a client-server application designed to provide a robust and accurate time tracking solution for artists in a visual effects pipeline. It addresses the limitations of generic time trackers by offering deep integration into core Digital Content Creation (DCC) applications, ensuring that time is logged automatically and accurately.

The system features:
- A central server
- A desktop client for artists
- A web-based dashboard for managers
- Direct integrations with Autodesk Maya and Blender

Key features include:
- User authentication
- Task-based tracking
- Automatic idle-time detection for data fidelity

## 2. Setup and Installation

To set up and run the project, you will need **Python 3** installed on your system.

### Step 2.1: Install All Dependencies

This project uses a single `requirements.txt` file to manage all necessary Python libraries for both the server and the client.

1. Navigate to the root directory of the project in your terminal (the `VFX_Time_Tracker` folder):

   ```bash
   cd path/to/your/VFX_Time_Tracker
   ```

2. Install all the required Python libraries at once by running:

   ```bash
   pip install -r requirements.txt
   ```

## 3. How to Run the Application

The application must be run in a specific order: the server must be running before the client or DCC integrations can connect.

### Step 3.1: Start the Server

1. Navigate to the `server` directory in your terminal.

2. Run the main `run.py` script:

   ```bash
   python run.py
   ```

   This script will:
   - Check if the database (`server_time_logs.db`) exists. If not, it will create and initialize it using `schema.sql`.
   - Start the Flask server. You should see output confirming the server is running on `http://127.0.0.1:5000`.

### Step 3.2: Run the Artist Client

1. Open a new terminal window.

2. Navigate to the `client` directory.

3. Run the `main.py` script:

   ```bash
   python main.py
   ```

   The artist's client application window will appear.

### Step 3.3: Install DCC Integrations

#### For Maya:

1. Copy the `dcc_client.py` file and the `maya_tracker_integration.py` file into your Maya scripts folder. This is typically located at:

   ```
   C:/Users/YOUR_USERNAME/OneDrive/Documents/maya/scripts/
   ```

#### For Blender:

1. The `vfx_tracker_addon` folder (containing `__init__.py` and a copy of `dcc_client.py`) needs to be installed as a Blender Add-on.

2. Right-click the `vfx_tracker_addon` folder and send it to a `.zip` file.

3. In Blender, go to **Edit > Preferences > Add-ons** and click "Install...".

4. Navigate to and select the `.zip` file you just created to install it.

5. Enable the "VFX Time Tracker" add-on in the list.

## 4. How to Use the Application

1. **Register a User**: Use the "Register" button in the Artist Client application to create a new user account (e.g., username: `mei`, password: `mei`).

2. **Launch a DCC**: Open either Maya or Blender.

3. **Log In**:
   - In Maya: A login window will appear.
   - In Blender: A login panel will appear in the sidebar (press `N`).
   - Log in with the credentials you just created.

4. **Select a Task & Start Tracking**: After logging in, select a task from the dropdown and start the session.

5. **Work and Go Idle**: As you work, heartbeats will be sent. If you leave the application idle for more than 10 minutes, the session will automatically pause and resume when you return.

6. **Stop Tracking**: Use the manual "Stop Tracking" button in the DCC to finalize your session.

7. **View Logs**: Open the Artist Client, log in, and select a date on the calendar to see your completed sessions and personal reports.

8. **View Manager Dashboard**: Click the "Launch Manager Web Dashboard" button in the client (or go to `http://127.0.0.1:5000/dashboard`) to see the high-level overview with charts and filtering options.
