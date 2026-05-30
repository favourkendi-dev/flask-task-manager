const API_URL = window.location.origin;

let token = localStorage.getItem('token');
let currentUser = localStorage.getItem('username');

// Check if already logged in
if (token && currentUser) {
    showTaskSection();
    loadTasks();
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

function showLogin() {
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
}

function showTaskSection() {
    document.getElementById('auth-section').style.display = 'none';
    document.getElementById('task-section').style.display = 'block';
    document.getElementById('user-display').textContent = 'Welcome, ' + currentUser + '!';
}

async function register() {
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    
    try {
        const response = await fetch(API_URL + '/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: username, password: password})
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Registered successfully! Please login.');
            showLogin();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(API_URL + '/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: username, password: password})
        });
        
        const data = await response.json();
        
        if (response.ok) {
            token = data.access_token;
            currentUser = data.username;
            localStorage.setItem('token', token);
            localStorage.setItem('username', currentUser);
            showTaskSection();
            loadTasks();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    document.getElementById('task-section').style.display = 'none';
    document.getElementById('auth-section').style.display = 'block';
    showLogin();
}

async function loadTasks() {
    try {
        const response = await fetch(API_URL + '/tasks', {
            headers: {'Authorization': 'Bearer ' + token}
        });
        
        const tasks = await response.json();
        
        if (response.ok) {
            displayTasks(tasks);
        } else {
            alert(tasks.error || 'Failed to load tasks');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function displayTasks(tasks) {
    const container = document.getElementById('tasks-container');
    container.innerHTML = '';
    
    if (tasks.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No tasks yet. Add one above!</p>';
        return;
    }
    
    tasks.forEach(function(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = 'task-item priority-' + task.priority + ' bg-white border border-gray-200 rounded-lg p-4 flex justify-between items-center' + (task.completed ? ' completed' : '');
        
        const dueDateText = task.due_date ? 'Due: ' + task.due_date : 'No due date';
        const priorityColor = task.priority === 'high' ? 'text-red-600' : task.priority === 'medium' ? 'text-yellow-600' : 'text-green-600';
        
        taskDiv.innerHTML = 
            '<div class="flex-1">' +
                '<h3 class="text-lg font-semibold text-gray-800 mb-1">' + task.title + '</h3>' +
                '<p class="text-gray-600 text-sm mb-2">' + (task.description || 'No description') + '</p>' +
                '<div class="flex gap-4 text-sm">' +
                    '<span class="' + priorityColor + ' font-medium capitalize">Priority: ' + task.priority + '</span>' +
                    '<span class="text-gray-500">' + dueDateText + '</span>' +
                '</div>' +
            '</div>' +
            '<div class="flex gap-2 ml-4">' +
                '<button onclick="toggleComplete(' + task.id + ')" ' +
                    'class="' + (task.completed ? 'bg-gray-500' : 'bg-blue-500') + ' text-white px-3 py-1 rounded hover:opacity-90 transition text-sm font-medium">' +
                    (task.completed ? 'Undo' : 'Complete') +
                '</button>' +
                '<button onclick="deleteTask(' + task.id + ')" ' +
                    'class="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 transition text-sm font-medium">' +
                    'Delete' +
                '</button>' +
            '</div>';
        
        container.appendChild(taskDiv);
    });
}

async function addTask() {
    const title = document.getElementById('task-title').value;
    const description = document.getElementById('task-description').value;
    const priority = document.getElementById('task-priority').value;
    const dueDate = document.getElementById('task-due-date').value;
    
    if (!title) {
        alert('Title is required');
        return;
    }
    
    try {
        const response = await fetch(API_URL + '/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                title: title,
                description: description,
                priority: priority,
                due_date: dueDate || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('task-title').value = '';
            document.getElementById('task-description').value = '';
            document.getElementById('task-due-date').value = '';
            loadTasks();
        } else {
            alert(data.error || 'Failed to add task');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function toggleComplete(taskId) {
    try {
        const response = await fetch(API_URL + '/tasks/' + taskId + '/complete', {
            method: 'PATCH',
            headers: {'Authorization': 'Bearer ' + token}
        });
        
        if (response.ok) {
            loadTasks();
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to update task');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(API_URL + '/tasks/' + taskId, {
            method: 'DELETE',
            headers: {'Authorization': 'Bearer ' + token}
        });
        
        if (response.ok) {
            loadTasks();
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to delete task');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}