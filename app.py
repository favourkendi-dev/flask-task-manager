from flask import Flask, jsonify, request, render_template, send_from_directory
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
jwt = JWTManager(app)

DATABASE = 'tasks.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

def get_current_user_id():
    return int(get_jwt_identity())

@app.route('/')
def hello():
    return {"message": "Hello, Task Manager is running!"}

@app.route('/app')
def frontend():
    return render_template('index.html')

# Serves static files on Render
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return jsonify({"error": "Username already exists"}), 409
        
        password_hash = generate_password_hash(password)
        created_at = datetime.now().isoformat()
        
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, created_at)
        )
        conn.commit()
        user_id = cursor.lastrowid
    
    return jsonify({
        "id": user_id,
        "username": username,
        "message": "User registered successfully"
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    access_token = create_access_token(identity=str(user['id']))
    
    return jsonify({
        "access_token": access_token,
        "user_id": user['id'],
        "username": username
    })

@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_current_user_id()
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
            "INSERT INTO tasks (user_id, title, description, completed, priority, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, title, description, 0, priority, due_date, created_at)
        )
        task_id = cursor.lastrowid
        conn.commit()
    
    return jsonify({
        "id": task_id,
        "user_id": user_id,
        "title": title,
        "description": description,
        "completed": False,
        "priority": priority,
        "due_date": due_date,
        "created_at": created_at
    }), 201

@app.route('/tasks', methods=['GET'])
@jwt_required()
def get_all_tasks():
    user_id = get_current_user_id()
    
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()
    
    tasks = []
    for row in rows:
        tasks.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "title": row["title"],
            "description": row["description"],
            "completed": bool(row["completed"]),
            "priority": row["priority"],
            "due_date": row["due_date"],
            "created_at": row["created_at"]
        })
    
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user_id = get_current_user_id()
    
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)).fetchone()
    
    if row is None:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify({
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"]
    })

@app.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_current_user_id()
    
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)).fetchone()
    
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
            "UPDATE tasks SET title = ?, description = ?, priority = ?, due_date = ? WHERE id = ? AND user_id = ?",
            (title, description, priority, due_date, task_id, user_id)
        )
        conn.commit()
    
    return jsonify({
        "id": task_id,
        "user_id": user_id,
        "title": title,
        "description": description,
        "completed": bool(row["completed"]),
        "priority": priority,
        "due_date": due_date,
        "created_at": row["created_at"]
    })

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_current_user_id()
    
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)).fetchone()
        if row is None:
            return jsonify({"error": "Task not found"}), 404
        
        conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        conn.commit()
    
    return jsonify({"message": f"Task {task_id} deleted successfully"}), 200

@app.route('/tasks/<int:task_id>/complete', methods=['PATCH'])
@jwt_required()
def toggle_complete(task_id):
    user_id = get_current_user_id()
    
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)).fetchone()
        if row is None:
            return jsonify({"error": "Task not found"}), 404
        
        new_status = not bool(row["completed"])
        conn.execute("UPDATE tasks SET completed = ? WHERE id = ? AND user_id = ?", (int(new_status), task_id, user_id))
        conn.commit()
    
    return jsonify({
        "id": task_id,
        "user_id": user_id,
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