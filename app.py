import sqlite3
import string
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'your_very_secret_key'
DATABASE = 'database.db'



def get_db_connection():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():

    conn = get_db_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            site TEXT NOT NULL,
            login TEXT NOT NULL,
            password TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()
    print("База данных инициализирована.")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        if not username or not password:
            return render_template('register.html', error='Заполните все поля')


        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, hashed_password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Пользователь существует')
        finally:
            conn.close()

        user = get_db_connection().execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        session['username'] = user['username']
        session['user_id'] = user['id']
        session['role'] = 'user'
        
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()


        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            session['user_id'] = user['id']
            session['role'] = 'user'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверный логин или пароль')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def index():
    if 'role' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    j = request.get_json() or {}
    try:
        L = int(j.get('length', 12))
    except (ValueError, TypeError):
        L = 12
    L = max(L, 1)

    chars = string.ascii_lowercase
    if j.get('uppercase'):
        chars += string.ascii_uppercase
    if j.get('numbers'):
        chars += string.digits
    if j.get('symbols'):
        chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    pwd = ''.join(random.choice(chars) for _ in range(L))
    site = j.get('site', '')
    login = j.get('login', '')
    user_id = session.get('user_id')

    if user_id and site and login:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO passwords (user_id, site, login, password, time) VALUES (?, ?, ?, ?, ?)',
            (user_id, site, login, pwd, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        conn.close()

    return jsonify({'password': pwd})


@app.route('/passwords')
def passwords():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session.get('user_id')
    if not user_id:
         return jsonify({'error': 'User not found'}), 401

    conn = get_db_connection()
    passwords_rows = conn.execute(
        'SELECT id, site, login, password, time FROM passwords WHERE user_id = ? ORDER BY id DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    

    user_passwords = [dict(row) for row in passwords_rows]
    return jsonify({'passwords': user_passwords})


@app.route('/delete_password', methods=['POST'])
def delete_password():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session.get('user_id')
    record_id = request.json.get('id')

    if user_id and record_id is not None:
        conn = get_db_connection()

        cursor = conn.execute(
            'DELETE FROM passwords WHERE id = ? AND user_id = ?',
            (record_id, user_id)
        )
        conn.commit()
        conn.close()
        if cursor.rowcount > 0: # Проверяем, была ли удалена строка
            return jsonify({'status': 'ok'})

    return jsonify({'error': 'Запись не найдена или отказано в доступе'}), 404


@app.route('/edit_password', methods=['POST'])
def edit_password():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session.get('user_id')
    j = request.json
    record_id = j.get('id')
    new_site = j.get('site')
    new_login = j.get('login')
    new_password = j.get('password')

    if user_id and record_id is not None:
        conn = get_db_connection()
        cursor = conn.execute(
            '''UPDATE passwords SET site = ?, login = ?, password = ?
               WHERE id = ? AND user_id = ?''',
            (new_site, new_login, new_password, record_id, user_id)
        )
        conn.commit()
        conn.close()
        if cursor.rowcount > 0:
            return jsonify({'status': 'ok'})

    return jsonify({'error': 'Запись не найдена или отказано в доступе'}), 404



if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8000, debug=True)