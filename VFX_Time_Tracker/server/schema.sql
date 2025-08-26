-- Drop existing tables if they exist to start fresh
DROP TABLE IF EXISTS activity_events;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tasks;

-- Users table to store artist login information
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table to store the list of possible tasks
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT UNIQUE NOT NULL
);

-- Sessions table to log the time for each work session
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_id INTEGER,
    app_name TEXT NOT NULL,
    session_name TEXT,
    scene_path TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    last_heartbeat TIMESTAMP,
    duration REAL, -- Total duration in minutes, excluding paused time
    paused_duration REAL DEFAULT 0, -- Total accumulated paused time in minutes
    status TEXT DEFAULT 'active', -- Can be 'active', 'paused', or 'stopped'
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (task_id) REFERENCES tasks (id)
);

-- Activity events for more detailed, granular tracking 
CREATE TABLE activity_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    event_data TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);

-- --- Initial Data ---
-- Insert some default tasks to get started
INSERT INTO tasks (task_name) VALUES ('Modeling');
INSERT INTO tasks (task_name) VALUES ('Texturing');
INSERT INTO tasks (task_name) VALUES ('Rigging');
INSERT INTO tasks (task_name) VALUES ('Animation');
INSERT INTO tasks (task_name) VALUES ('Lighting');
INSERT INTO tasks (task_name) VALUES ('Compositing');
INSERT INTO tasks (task_name) VALUES ('General');
