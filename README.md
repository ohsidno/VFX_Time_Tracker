# VFX Time Tracker

## 1. Project Overview
The **VFX Time Tracker** is a client-server application designed to provide a robust and accurate time tracking solution for artists in a visual effects (VFX) pipeline.  

Unlike generic time trackers, this system offers deep integration into core Digital Content Creation (DCC) applications, ensuring time is logged **automatically and accurately**.  

**Key Components:**
- **Central Server** (Flask-based backend with SQLite database)
- **Desktop Client** for artists
- **Web-based Manager Dashboard**
- **Direct Integrations** with Autodesk Maya and Blender

**Key Features:**
- User authentication
- Task-based time tracking
- Automatic idle-time detection
- Centralized logging for managers

---

## 2. Setup and Installation

### Requirements
- Python 3.x installed on your system
- `requirements.txt` for dependencies

### Step 2.1: Install Dependencies
Navigate to the project root (`VFX_Time_Tracker`) and install all dependencies:

```bash
cd path/to/your/VFX_Time_Tracker
pip install -r requirements.txt
