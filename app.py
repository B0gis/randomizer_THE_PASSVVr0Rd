import os
import json
import random
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'secret'

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data.json')


def load_data():
    if not os.path.exists(DATA_PATH):
        return {"users": {}, "passwords": {}, "site": {}}
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"users": {}, "passwords": {}, "site": {}}


def save_data(d):
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = (request.form.get('username') or '').strip()
        p = request.form.get('password') or ''
        if not u or not p:
            return render_template('register.html', error='Заполните все поля')
        data = load_data()
        if u in data['users']:
            return render_template('register.html', error='Пользователь существует')
        data['users'][u] = p
        data.setdefault('passwords', {}).setdefault(u, [])
        save_data(data)
        session['username'] = u
        session['role'] = 'user'
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = (request.form.get('username') or '').strip()
        p = request.form.get('password') or ''
        data = load_data()
        if data['users'].get(u) == p:
            session['username'] = u
            session['role'] = 'user'
            return redirect(url_for('index'))
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
    except:
        L = 12
    if L < 1:
        L = 1
    chars = 'abcdefghijklmnopqrstuvwxyz'
    if j.get('uppercase'):
        chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if j.get('numbers'):
        chars += '0123456789'
    if j.get('symbols'):
        chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
    if not chars:
        chars = 'abcdefghijklmnopqrstuvwxyz'
    pwd = ''.join(random.choice(chars) for _ in range(L))

    site = j.get('site', '')
    login = j.get('login', '')

    data = load_data()
    u = session.get('username')
    if u:
        data.setdefault('passwords', {}).setdefault(u, []).append({
            'password': pwd,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'site': site,
            'login': login
        })
        save_data(data)
        print(f"Site: {site}, Login: {login}")
    return jsonify({'password': pwd})


@app.route('/passwords')
def passwords():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_data()
    u = session.get('username')
    user_passwords = data.get('passwords', {}).get(u, [])
    return jsonify({'passwords': user_passwords})


@app.route('/delete_password', methods=['POST'])
def delete_password():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_data()
    u = session.get('username')
    record_id = request.json.get('id')
    if u and record_id is not None:
        user_passwords = data.get('passwords', {}).get(u, [])
        if 0 <= record_id < len(user_passwords):
            user_passwords.pop(record_id)
            save_data(data)
            return jsonify({'status': 'ok'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/edit_password', methods=['POST'])
def edit_password():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_data()
    u = session.get('username')
    record_id = request.json.get('id')
    new_site = request.json.get('site')
    new_login = request.json.get('login')
    new_password = request.json.get('password')
    if u and record_id is not None:
        user_passwords = data.get('passwords', {}).get(u, [])
        if 0 <= record_id < len(user_passwords):
            user_passwords[record_id]['site'] = new_site
            user_passwords[record_id]['login'] = new_login
            user_passwords[record_id]['password'] = new_password
            save_data(data)
            return jsonify({'status': 'ok'})
    return jsonify({'error': 'Not found'}), 404




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
