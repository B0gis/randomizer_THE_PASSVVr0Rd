from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
users = {
    "123": "123"
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['role'] = 'user'
            return redirect(url_for('main_page'))
        else:
            return render_template('login.html', error="Неверный логин или пароль")
    return render_template('login.html')

@app.route('/')
def main_page():
    if 'role' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def make_pass():
    if 'role' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    try:
        pass_len = int(data.get('length', 12))
    except:
        pass_len = 8

    if pass_len < 4:
        pass_len = 4
    if pass_len > 100:
        pass_len = 100

    use_upper = data.get('uppercase', False)
    use_digits = data.get('numbers', False)
    use_symbols = data.get('symbols', False)

    chars = 'abcdefghijklmnopqrstuvwxyz'
    if use_upper:
        chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if use_digits:
        chars += '0123456789'
    if use_symbols:
        chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'

    if not chars:
        chars = 'abcdefghijklmnopqrstuvwxyz'

    password = ''.join(random.choice(chars) for _ in range(pass_len))
    return jsonify({'password': password})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)