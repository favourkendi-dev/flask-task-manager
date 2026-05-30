from flask import Flask, jsonify, request
from datetime import datetime
import os
import sqlite3

app = Flask(__name__)

DATABASE = 'tasks.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()

@app.route('/')
def hello():
    return {"message": "Hello, Task Manager is running!"}

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    if not data or not data.get("title"):
        return jsonify({"error": "Title is required"}), 400
    
    title = data.get("title")
    description = data.get("description", "")
    priority = data.get("priority", "medium")
    due_date = data.get("due_date", None)
    created_at = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, completed, priority, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, 0, priority, due_date, created_at)
        )
        task_id = cursor.lastrowid
        conn.commit()
    
    return jsonify({
        "id": task_id,
        "title": title,
        "description": description,
        "completed": False,
        "priority": priority,
        "due_date": due_date,
        "created_at": created_at
    }), 201

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    
    tasks = []
    for row in rows:
        tasks.append({
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "completed": bool(row["completed"]),
            "priority": row["priority"],
            "due_date": row["due_date"],
            "created_at": row["created_at"]
        })
    
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    
    if row is None:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify({
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"]
    })

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    
    if row is None:
        return jsonify({"error": "Task not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    title = data.get("title", row["title"])
    description = data.get("description", row["description"])
    priority = data.get("priority", row["priority"])
    due_date = data.get("due_date", row["due_date"])
    
    with get_db() as conn:
        conn.execute(
            "UPDATE tasks SET title = ?, description = ?, priority = ?, due_date = ? WHERE id = ?",
            (title, description, priority, due_date, task_id)
        )
        conn.commit()
    
    return jsonify({
        "id": task_id,
        "title": title,
        "description": description,
        "completed": bool(row["completed"]),
        "priority": priority,
        "due_date": due_date,
        "created_at": row["created_at"]
    })

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Task not found"}), 404
        
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    
    return jsonify({"message": f"Task {task_id} deleted successfully"}), 200

@app.route('/tasks/<int:task_id>/complete', methods=['PATCH'])
def toggle_complete(task_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Task not found"}), 404
        
        new_status = not bool(row["completed"])
        conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (int(new_status), task_id))
        conn.commit()
    
    return jsonify({
        "id": task_id,
        "title": row["title"],
        "description": row["description"],
        "completed": new_status,
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"]
    })

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)