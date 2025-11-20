##--- START OF FILE db.py ---

import sqlite3
from datetime import datetime

DB_NAME = "studio.db"

def init_db():
    """Creates the projects table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            project_name TEXT,
            user_request TEXT,
            research_output TEXT,
            script_content TEXT,
            editor_feedback TEXT,
            editor_score INTEGER,
            is_approved INTEGER,
            storyboard_output TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_project(user_request: str):
    """Creates a new project record and returns the new ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Generate a simple name
    project_name = (user_request[:30] + '...') if len(user_request) > 30 else user_request
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute('''
        INSERT INTO projects (created_at, project_name, user_request, is_approved, editor_score)
        VALUES (?, ?, ?, 0, 0)
    ''', (created_at, project_name, user_request))
    
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_project_field(project_id, field_name, value):
    """Updates a specific column for a specific project."""
    if not project_id:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = f"UPDATE projects SET {field_name} = ? WHERE id = ?"
    c.execute(query, (value, project_id))
    conn.commit()
    conn.close()

def update_editor_stats(project_id, feedback, score, approved):
    """Updates multiple editor fields at once."""
    if not project_id:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    is_approved_int = 1 if approved else 0
    c.execute('''
        UPDATE projects 
        SET editor_feedback = ?, editor_score = ?, is_approved = ?
        WHERE id = ?
    ''', (feedback, score, is_approved_int, project_id))
    conn.commit()
    conn.close()

def get_all_projects():
    """Returns a list of (id, project_name, created_at)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, project_name, created_at FROM projects ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def load_project(project_id):
    """Returns the full row for a specific project."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None