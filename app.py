from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, flask is working"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

from flask import Flask
from flask import Flask, render_template, redirect, url_for, request, session
from flask_mysqldb import MySQL
from config import Config
import MySQLdb.cursors
import re
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)

# Decorator for route protection
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and all(field in request.form for field in ['name', 'email', 'password']):
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Email is already registered!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not name or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, password))
            mysql.connection.commit()
            message = 'You have successfully registered!'
            return redirect(url_for('login'))
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and all(field in request.form for field in ['email', 'password']):
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['name'] = account['name']
            return redirect(url_for('dashboard'))
        else:
            message = 'Incorrect credentials!'
    return render_template('login.html', message=message)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM projects WHERE user_id = %s', (session['id'],))
    projects = cursor.fetchall()
    return render_template('dashboard.html', name=session['name'], projects=projects)

@app.route('/project/create', methods=['GET', 'POST'])
@login_required
def crear_proyecto():
    if request.method == 'POST' and all(field in request.form for field in ['title', 'description', 'start_date']):
        title = request.form['title']
        description = request.form['description']
        start_date = request.form['start_date']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO projects (user_id, title, description, start_date) VALUES (%s, %s, %s, %s)', (session['id'], title, description, start_date))
        mysql.connection.commit()
        flash('Proyecto creado exitosamente.')
        return redirect(url_for('dashboard'))
    return render_template('crear_proyecto.html')

@app.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_proyecto(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and all(field in request.form for field in ['title', 'description', 'start_date']):
        title = request.form['title']
        description = request.form['description']
        start_date = request.form['start_date']
        completed = 'completed' in request.form
        cursor.execute('UPDATE projects SET title=%s, description=%s, start_date=%s, completed=%s WHERE id=%s AND user_id=%s', (title, description, start_date, completed, id, session['id']))
        mysql.connection.commit()
        return redirect(url_for('dashboard'))
    cursor.execute('SELECT * FROM projects WHERE id = %s AND user_id = %s', (id, session['id']))
    project = cursor.fetchone()
    return render_template('editar_proyecto.html', project=project)

@app.route('/project/delete/<int:id>', methods=['POST'])
@login_required
def delete_project(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tasks WHERE project_id = %s', (id,))
    tasks = cursor.fetchall()
    if tasks:
        message = 'Cannot delete project with assigned tasks.'
        return redirect(url_for('dashboard', message=message))
    cursor.execute('DELETE FROM projects WHERE id = %s AND user_id = %s', (id, session['id']))
    mysql.connection.commit()
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

