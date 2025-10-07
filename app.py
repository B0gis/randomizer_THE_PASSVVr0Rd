from flask import Flask, render_template, request, jsonify
import sqlite3
import random

app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def make_pass():
    data = request.get_json()

    try:
        pass_len = int(data.get('length', 12))
    except:
        pass_len = 12

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

    password = ''
    for _ in range(pass_len):
        password += random.choice(chars)

    return jsonify({'password': password})
    
if __name__ == '__main__':
    app.run(debug=True)