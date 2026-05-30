import pytest
import app as app_module
import os

@pytest.fixture
def client():
    if os.path.exists('tasks.db'):
        os.remove('tasks.db')
    
    app_module.init_db()
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client

def get_auth_token(client, username="testuser", password="testpass"):
    client.post('/register', json={"username": username, "password": password})
    response = client.post('/login', json={"username": username, "password": password})
    return response.get_json()["access_token"]

def test_hello(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello, Task Manager is running!"}

def test_register(client):
    response = client.post('/register', json={"username": "john", "password": "secret"})
    assert response.status_code == 201
    assert response.get_json()["username"] == "john"

def test_register_duplicate(client):
    client.post('/register', json={"username": "john", "password": "secret"})
    response = client.post('/register', json={"username": "john", "password": "secret"})
    assert response.status_code == 409

def test_login(client):
    client.post('/register', json={"username": "john", "password": "secret"})
    response = client.post('/login', json={"username": "john", "password": "secret"})
    assert response.status_code == 200
    assert "access_token" in response.get_json()

def test_login_invalid(client):
    response = client.post('/login', json={"username": "nobody", "password": "wrong"})
    assert response.status_code == 401

def test_create_task(client):
    token = get_auth_token(client)
    response = client.post('/tasks', 
        json={"title": "Test task", "description": "Test", "priority": "high"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Test task"
    assert data["user_id"] == 1

def test_create_task_unauthorized(client):
    response = client.post('/tasks', json={"title": "Test"})
    assert response.status_code == 401

def test_get_all_tasks(client):
    token = get_auth_token(client)
    client.post('/tasks', json={"title": "Task 1"}, headers={"Authorization": f"Bearer {token}"})
    client.post('/tasks', json={"title": "Task 2"}, headers={"Authorization": f"Bearer {token}"})
    response = client.get('/tasks', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.get_json()) == 2

def test_get_task(client):
    token = get_auth_token(client)
    client.post('/tasks', json={"title": "Single"}, headers={"Authorization": f"Bearer {token}"})
    response = client.get('/tasks/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["title"] == "Single"

def test_get_task_not_found(client):
    token = get_auth_token(client)
    response = client.get('/tasks/999', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_update_task(client):
    token = get_auth_token(client)
    client.post('/tasks', json={"title": "Old"}, headers={"Authorization": f"Bearer {token}"})
    response = client.put('/tasks/1', json={"title": "New"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["title"] == "New"

def test_toggle_complete(client):
    token = get_auth_token(client)
    client.post('/tasks', json={"title": "Complete"}, headers={"Authorization": f"Bearer {token}"})
    response = client.patch('/tasks/1/complete', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["completed"] == True

def test_delete_task(client):
    token = get_auth_token(client)
    client.post('/tasks', json={"title": "Delete"}, headers={"Authorization": f"Bearer {token}"})
    response = client.delete('/tasks/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["message"] == "Task 1 deleted successfully"

def test_other_user_cannot_access_task(client):
    token1 = get_auth_token(client, "user1", "pass1")
    client.post('/tasks', json={"title": "Private"}, headers={"Authorization": f"Bearer {token1}"})
    
    token2 = get_auth_token(client, "user2", "pass2")
    response = client.get('/tasks/1', headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 404