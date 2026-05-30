import pytest
import app as app_module
import os

@pytest.fixture
def client():
    # Remove old test database if exists
    if os.path.exists('tasks.db'):
        os.remove('tasks.db')
    
    # Reinitialize database
    app_module.init_db()
    
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client

def test_hello(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello, Task Manager is running!"}

def test_create_task(client):
    response = client.post('/tasks', json={
        "title": "Test task",
        "description": "Test description",
        "priority": "high",
        "due_date": "2026-06-01"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Test task"
    assert data["description"] == "Test description"
    assert data["completed"] == False
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-06-01"
    assert data["id"] == 1

def test_create_task_missing_title(client):
    response = client.post('/tasks', json={"description": "No title"})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Title is required"}

def test_get_all_tasks(client):
    client.post('/tasks', json={"title": "Task 1"})
    client.post('/tasks', json={"title": "Task 2"})
    response = client.get('/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2

def test_get_task(client):
    client.post('/tasks', json={"title": "Single task"})
    response = client.get('/tasks/1')
    assert response.status_code == 200
    assert response.get_json()["title"] == "Single task"

def test_get_task_not_found(client):
    response = client.get('/tasks/999')
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_update_task(client):
    client.post('/tasks', json={"title": "Old title"})
    response = client.put('/tasks/1', json={"title": "New title"})
    assert response.status_code == 200
    assert response.get_json()["title"] == "New title"

def test_update_task_not_found(client):
    response = client.put('/tasks/999', json={"title": "New title"})
    assert response.status_code == 404

def test_toggle_complete(client):
    client.post('/tasks', json={"title": "Complete me"})
    response = client.patch('/tasks/1/complete')
    assert response.status_code == 200
    assert response.get_json()["completed"] == True

def test_toggle_complete_not_found(client):
    response = client.patch('/tasks/999/complete')
    assert response.status_code == 404

def test_delete_task(client):
    client.post('/tasks', json={"title": "Delete me"})
    response = client.delete('/tasks/1')
    assert response.status_code == 200
    assert response.get_json()["message"] == "Task 1 deleted successfully"

def test_delete_task_not_found(client):
    response = client.delete('/tasks/999')
    assert response.status_code == 404