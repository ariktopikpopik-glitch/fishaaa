from flask import Flask, send_from_directory
import os
import sys

app = Flask(__name__)

@app.route('/')
def hello():
    # Пытаемся вернуть index.html, если он есть
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    else:
        return "Flask app is running on Render!", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    # Это важно: Render ожидает именно 0.0.0.0
    # Переменная PORT приходит от Render, по умолчанию 10000
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask app on port {port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port)
