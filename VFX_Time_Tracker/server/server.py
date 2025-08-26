import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)
DATABASE = "server_time_logs.db"

# Database Functions 
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

#  Web Page Route 
@app.route('/dashboard')
def dashboard():
    """Serves the main manager dashboard web page."""
    return render_template('index.html')


#  API Endpoints 

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db()
    rows = conn.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    conn.close()
    users = [dict(row) for row in rows]
    return jsonify({"status": "success", "users": users})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = get_db()
    rows = conn.execute("SELECT id, task_name FROM tasks ORDER BY task_name").fetchall()
    conn.close()
    tasks = [dict(row) for row in rows]
    return jsonify({"status": "success", "tasks": tasks})


@app.route('/api/dashboard_stats', methods=['GET'])
def dashboard_stats():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    artist_username = request.args.get('artist')

    conn = get_db()
    
    base_query = """
        SELECT u.username, s.app_name, s.duration, t.task_name, s.session_name, s.end_time
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN tasks t ON s.task_id = t.id
        WHERE s.status = 'stopped' AND s.duration IS NOT NULL
    """
    params = []
    if start_date:
        base_query += " AND date(s.start_time) >= ?"
        params.append(start_date)
    if end_date:
        base_query += " AND date(s.start_time) <= ?"
        params.append(end_date)
    if artist_username:
        base_query += " AND u.username = ?"
        params.append(artist_username)

    df = pd.read_sql_query(base_query, conn, params=tuple(params))
    conn.close()

    if df.empty:
        stats = {
            "total_hours": 0, "top_artist": "N/A", "hours_per_artist": [],
            "hours_per_app": [], "hours_per_task": [], "recent_sessions": [],
            "all_sessions_for_export": []
        }
        return jsonify({"status": "success", "stats": stats})

    total_hours = df['duration'].sum() / 60
    hours_per_artist = df.groupby('username')['duration'].sum().div(60).reset_index(name='total_duration').sort_values(by='total_duration', ascending=False)
    hours_per_app = df.groupby('app_name')['duration'].sum().div(60).reset_index(name='total_duration').sort_values(by='total_duration', ascending=False)
    hours_per_task = df.groupby('task_name')['duration'].sum().div(60).reset_index(name='total_duration').sort_values(by='total_duration', ascending=False)
    top_artist = hours_per_artist.iloc[0]['username'] if not hours_per_artist.empty else "N/A"
    recent_sessions_df = df.sort_values(by='end_time', ascending=False).head(5)

    stats = {
        "total_hours": total_hours, "top_artist": top_artist,
        "hours_per_artist": hours_per_artist.to_dict('records'),
        "hours_per_app": hours_per_app.to_dict('records'),
        "hours_per_task": hours_per_task.to_dict('records'),
        "recent_sessions": recent_sessions_df.to_dict('records'),
        "all_sessions_for_export": df.to_dict('records')
    }
    return jsonify({"status": "success", "stats": stats})


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = get_db()
    if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        conn.close()
        return jsonify({"status": "error", "message": f"User {username} is already registered."}), 409
    conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                 (username, generate_password_hash(password)))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "User created successfully."}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user is None or not check_password_hash(user['password_hash'], password):
        return jsonify({"status": "error", "message": "Invalid username or password."}), 401
    return jsonify({"status": "success", "user": {"id": user['id'], "username": user['username']}})

@app.route('/api/session/start', methods=['POST'])
def session_start():
    data = request.get_json()
    now = datetime.utcnow()
    conn = get_db()
    cursor = conn.cursor()
    user_id = data.get('user_id')
    task_id = data.get('task_id')

    if not user_id:
        conn.close()
        return jsonify({"status": "error", "message": "user_id is required."}), 400

    cursor.execute(
        "INSERT INTO sessions (user_id, task_id, app_name, session_name, scene_path, start_time, last_heartbeat) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, task_id, data.get('dcc_name'), data.get('project_name'), data.get('scene_name'), now, now)
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return jsonify({"status": "success", "session_id": session_id}), 201

@app.route('/api/session/pause', methods=['POST'])
def session_pause():
    data = request.get_json()
    session_id = data.get('session_id')
    conn = get_db()
    conn.execute('UPDATE sessions SET status = "paused", last_heartbeat = ? WHERE id = ? AND status = "active"',
                 (datetime.utcnow(), session_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "session_paused"})

@app.route('/api/session/resume', methods=['POST'])
def session_resume():
    data = request.get_json()
    session_id = data.get('session_id')
    conn = get_db()
    
    session = conn.execute('SELECT last_heartbeat, paused_duration FROM sessions WHERE id = ? AND status = "paused"', (session_id,)).fetchone()
    if not session:
        conn.close()
        return jsonify({"status": "error", "message": "Session not found or not paused"}), 404

    pause_start_time = datetime.fromisoformat(session['last_heartbeat'])
    resume_time = datetime.utcnow()
    pause_duration_seconds = (resume_time - pause_start_time).total_seconds()
    
    new_total_paused_duration = (session['paused_duration'] or 0) + (pause_duration_seconds / 60)

    conn.execute('UPDATE sessions SET status = "active", last_heartbeat = ?, paused_duration = ? WHERE id = ?',
                 (resume_time, new_total_paused_duration, session_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "session_resumed"})


@app.route('/api/session/heartbeat', methods=['POST'])
def session_heartbeat():
    data = request.get_json()
    conn = get_db()
    conn.execute('UPDATE sessions SET last_heartbeat = ? WHERE id = ? AND status = "active"',
                 (datetime.utcnow(), data.get('session_id')))
    conn.commit()
    conn.close()
    return jsonify({"status": "acknowledged"})

@app.route('/api/session/stop', methods=['POST'])
def session_stop():
    data = request.get_json()
    session_id = data.get('session_id')
    conn = get_db()
    session = conn.execute('SELECT start_time, paused_duration FROM sessions WHERE id = ?', (session_id,)).fetchone()
    if not session:
        conn.close()
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    start_time = datetime.fromisoformat(session['start_time'])
    end_time = datetime.utcnow()
    total_paused_duration_minutes = session['paused_duration'] or 0
    
    total_duration_minutes = (end_time - start_time).total_seconds() / 60
    active_duration = round(total_duration_minutes - total_paused_duration_minutes, 2)
    
    conn.execute('UPDATE sessions SET end_time = ?, duration = ?, status = "stopped" WHERE id = ?',
                 (end_time, active_duration, session_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "session_stopped"})

@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    user_id = request.args.get('user_id')
    date = request.args.get('date')
    conn = get_db()
    rows = conn.execute("""
        SELECT s.id, u.username, s.app_name, s.session_name, t.task_name, s.start_time, s.end_time, s.duration
        FROM sessions s 
        JOIN users u ON s.user_id = u.id
        LEFT JOIN tasks t ON s.task_id = t.id
        WHERE s.user_id = ? AND date(s.start_time) = ? AND s.status = "stopped"
        ORDER BY s.start_time
    """, (user_id, date)).fetchall()
    conn.close()
    logs = [dict(row) for row in rows]
    return jsonify({"status": "success", "logs": logs})

@app.route('/api/get_session_events', methods=['GET'])
def get_session_events():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"status": "error", "message": "session_id parameter is required"}), 400
    conn = get_db()
    rows = conn.execute("SELECT timestamp, event_type, event_data FROM activity_events WHERE session_id = ? ORDER BY timestamp",
                        (session_id,)).fetchall()
    conn.close()
    events = [dict(row) for row in rows]
    return jsonify({"status": "success", "events": events})
