import os
import sqlite3
from server import app # Flask app instance from server.py

# Config
DATABASE = "server_time_logs.db"
SCHEMA = "schema.sql"

def initialize_database():
    """
    Checks if the database file exists. If not, it creates it
    and populates it with the schema from schema.sql.
    """
    if not os.path.exists(DATABASE):
        print(f"Database not found at '{DATABASE}'. Initializing...")
        try:
            conn = sqlite3.connect(DATABASE)
            
            with open(SCHEMA, 'r') as f:
                conn.cursor().executescript(f.read())
            
            conn.commit()
            conn.close()
            print("Database initialized successfully.")
        except FileNotFoundError:
            print(f"ERROR: Could not find '{SCHEMA}'. Please ensure it is in the same directory.")
            exit()
        except Exception as e:
            print(f"An error occurred during database initialization: {e}")
            exit()
    else:
        print("Database already exists. Skipping initialization.")

if __name__ == '__main__':
    
    initialize_database()
    
    print("Starting VFX Time Tracker server...")
    print("Access the Manager Dashboard at http://127.0.0.1:5000/dashboard")
    app.run(host='0.0.0.0', port=5000, debug=False)

