from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# In-memory storage for tasks
tasks = []
task_id_counter = 1

@app.route('/')
def hello():
    return {"message": "Hello, Task Manager is running!"}

@app.route('/tasks', methods=['POST'])
def create_task():
    global task_id_counter
    
    data = request.get_json()
    
    # Validation
    if not data or not data.get("title"):
        return jsonify({"error": "Title is required"}), 400
    
    new_task = {
        "id": task_id_counter,
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    
    tasks.append(new_task)
    task_id_counter += 1
    
    return jsonify(new_task), 201

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(task)

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    task["title"] = data.get("title", task["title"])
    task["description"] = data.get("description", task["description"])
    
    return jsonify(task)

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    global tasks
    
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    
    tasks = [t for t in tasks if t["id"] != task_id]
    
    return jsonify({"message": f"Task {task_id} deleted successfully"}), 200

@app.route('/tasks/<int:task_id>/complete', methods=['PATCH'])
def toggle_complete(task_id):
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    
    task["completed"] = not task["completed"]
    
    return jsonify(task)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')