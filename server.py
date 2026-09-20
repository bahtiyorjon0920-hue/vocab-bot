import os
import sys
import json
import time
import threading
import urllib.request
import urllib.parse
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from db import Database

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()

PORT = int(os.getenv('PORT', 3000))
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID = str(os.getenv('ADMIN_ID', '')).strip()
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin').strip().replace('@', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', f'http://localhost:{PORT}').strip()
CARD_NUMBER = os.getenv('CARD_NUMBER', '5614 6820 5096 7480').strip()
PRICE_UZS = os.getenv('PRICE_PER_MONTH', '50 000').strip()
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')

class VocabHTTPHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self._set_cors()
        self.end_headers()
        self.wfile.write(body)

    def send_file_response(self, file_path):
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            file_path = os.path.join(PUBLIC_DIR, 'index.html')
        if not os.path.exists(file_path):
            self.send_error(404, 'File Not Found')
            return
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'
        with open(file_path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.send_header('Content-Length', str(len(content)))
        self._set_cors()
        self.end_headers()
        self.wfile.write(content)

    def send_html(self, status, html_content):
        body = html_content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self._set_cors()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        clean_card = CARD_NUMBER.replace(' ', '')

        if path == '/pay/click':
            html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Click ilovasida to'lash</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    body {{ background: #0b1329; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
    .card {{ background: #1e293b; border: 1px solid rgba(255,255,255,0.12); border-radius: 28px; padding: 32px 24px; max-width: 420px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6); }}
    .icon {{ width: 72px; height: 72px; border-radius: 20px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center; font-size: 38px; background: rgba(0, 184, 148, 0.15); border: 2px solid #00b894; }}
    h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 8px; color: #fff; }}
    p {{ font-size: 14px; color: #94a3b8; margin-bottom: 22px; }}
    .info-box {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 18px; margin-bottom: 22px; text-align: left; }}
    .info-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; }}
    .info-label {{ color: #94a3b8; }}
    .info-val {{ font-weight: 700; color: #fff; }}
    .card-num {{ font-size: 18px; letter-spacing: 1px; color: #38bdf8; font-family: monospace; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: space-between; margin-top: 6px; background: rgba(56,189,248,0.08); padding: 10px 14px; border-radius: 12px; border: 1px dashed rgba(56,189,248,0.4); }}
    .btn {{ display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 16px; border-radius: 16px; font-weight: 800; font-size: 16px; text-decoration: none; border: none; cursor: pointer; transition: 0.2s; margin-bottom: 12px; }}
    .btn-main {{ background: #00b894; color: #fff; box-shadow: 0 10px 20px rgba(0, 184, 148, 0.3); }}
    .btn-main:active {{ transform: scale(0.98); }}
    .btn-sub {{ background: rgba(255,255,255,0.08); color: #f8fafc; font-size: 14px; font-weight: 600; }}
    .toast {{ display: none; margin-bottom: 16px; padding: 10px; background: #22c55e; color: #fff; border-radius: 10px; font-size: 14px; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">🟢</div>
    <h1>Click orqali to'lov</h1>
    <p>Click SuperApp ilovasi ochilmoqda...</p>

    <div id="toast" class="toast">✅ Karta raqami nusxalandi!</div>

    <div class="info-box">
      <div class="info-row">
        <span class="info-label">To'lov miqdori:</span>
        <span class="info-val">50 000 so'm</span>
      </div>
      <div>
        <span class="info-label" style="font-size: 13px;">Karta raqami (bosib nusxalang):</span>
        <div class="card-num" onclick="copyCard()">
          <span>{clean_card}</span>
          <span style="font-size: 12px; background: #38bdf8; color: #000; padding: 2px 8px; border-radius: 6px; font-family: sans-serif;">Nusxalash 📋</span>
        </div>
      </div>
    </div>

    <a href="intent://my.click.uz/services/p2p?card_num={clean_card}&amount=50000#Intent;package=uz.click.app;scheme=https;end;" id="openAppBtn" class="btn btn-main">
      📲 Click ilovasida ochish
    </a>

    <a href="https://my.click.uz/services/p2p?card_num={clean_card}&amount=50000" class="btn btn-sub">
      🌐 Brauzerda ochish
    </a>

    <a href="https://t.me/clickuz" class="btn btn-sub" style="background: rgba(56,189,248,0.12); color: #38bdf8;">
      🤖 @clickuz Telegram bot orqali to'lash
    </a>
  </div>

  <script>
    function copyCard() {{
      const card = "{clean_card}";
      if (navigator.clipboard) {{
        navigator.clipboard.writeText(card);
      }}
      const t = document.getElementById('toast');
      t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 3000);
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      const isAndroid = /Android/i.test(navigator.userAgent);
      const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
      const intentUrl = "intent://my.click.uz/services/p2p?card_num={clean_card}&amount=50000#Intent;package=uz.click.app;scheme=https;end;";
      const schemeUrl = "click://pay/p2p?card={clean_card}&amount=50000";
      const webUrl = "https://my.click.uz/services/p2p?card_num={clean_card}&amount=50000";

      if (isAndroid) {{
        window.location.href = intentUrl;
      }} else if (isIOS) {{
        window.location.href = schemeUrl;
        setTimeout(() => {{ window.location.href = webUrl; }}, 1500);
      }} else {{
        window.location.href = webUrl;
      }}
    }});
  </script>
</body>
</html>"""
            return self.send_html(200, html)

        elif path == '/pay/payme':
            html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Payme ilovasida to'lash</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    body {{ background: #0b1329; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
    .card {{ background: #1e293b; border: 1px solid rgba(255,255,255,0.12); border-radius: 28px; padding: 32px 24px; max-width: 420px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6); }}
    .icon {{ width: 72px; height: 72px; border-radius: 20px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center; font-size: 38px; background: rgba(0, 194, 203, 0.15); border: 2px solid #00c2cb; }}
    h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 8px; color: #fff; }}
    p {{ font-size: 14px; color: #94a3b8; margin-bottom: 22px; }}
    .info-box {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 18px; margin-bottom: 22px; text-align: left; }}
    .info-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; }}
    .info-label {{ color: #94a3b8; }}
    .info-val {{ font-weight: 700; color: #fff; }}
    .card-num {{ font-size: 18px; letter-spacing: 1px; color: #38bdf8; font-family: monospace; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: space-between; margin-top: 6px; background: rgba(56,189,248,0.08); padding: 10px 14px; border-radius: 12px; border: 1px dashed rgba(56,189,248,0.4); }}
    .btn {{ display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 16px; border-radius: 16px; font-weight: 800; font-size: 16px; text-decoration: none; border: none; cursor: pointer; transition: 0.2s; margin-bottom: 12px; }}
    .btn-main {{ background: #00c2cb; color: #fff; box-shadow: 0 10px 20px rgba(0, 194, 203, 0.3); }}
    .btn-main:active {{ transform: scale(0.98); }}
    .btn-sub {{ background: rgba(255,255,255,0.08); color: #f8fafc; font-size: 14px; font-weight: 600; }}
    .toast {{ display: none; margin-bottom: 16px; padding: 10px; background: #22c55e; color: #fff; border-radius: 10px; font-size: 14px; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">🔵</div>
    <h1>Payme orqali to'lov</h1>
    <p>Payme ilovasi ochilmoqda...</p>

    <div id="toast" class="toast">✅ Karta raqami nusxalandi!</div>

    <div class="info-box">
      <div class="info-row">
        <span class="info-label">To'lov miqdori:</span>
        <span class="info-val">50 000 so'm</span>
      </div>
      <div>
        <span class="info-label" style="font-size: 13px;">Karta raqami (bosib nusxalang):</span>
        <div class="card-num" onclick="copyCard()">
          <span>{clean_card}</span>
          <span style="font-size: 12px; background: #38bdf8; color: #000; padding: 2px 8px; border-radius: 6px; font-family: sans-serif;">Nusxalash 📋</span>
        </div>
      </div>
    </div>

    <a href="intent://payme.uz/{clean_card}/50000#Intent;package=uz.dida.payme;scheme=https;end;" id="openAppBtn" class="btn btn-main">
      📲 Payme ilovasida ochish
    </a>

    <a href="https://payme.uz/{clean_card}/50000" class="btn btn-sub">
      🌐 Brauzerda ochish
    </a>
  </div>

  <script>
    function copyCard() {{
      const card = "{clean_card}";
      if (navigator.clipboard) {{
        navigator.clipboard.writeText(card);
      }}
      const t = document.getElementById('toast');
      t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 3000);
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      const isAndroid = /Android/i.test(navigator.userAgent);
      const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
      const intentUrl = "intent://payme.uz/{clean_card}/50000#Intent;package=uz.dida.payme;scheme=https;end;";
      const schemeUrl = "payme://transfer?card={clean_card}&amount=50000";
      const webUrl = "https://payme.uz/{clean_card}/50000";

      if (isAndroid) {{
        window.location.href = intentUrl;
      }} else if (isIOS) {{
        window.location.href = schemeUrl;
        setTimeout(() => {{ window.location.href = webUrl; }}, 1500);
      }} else {{
        window.location.href = webUrl;
      }}
    }});
  </script>
</body>
</html>"""
            return self.send_html(200, html)

        elif path == '/api/get-words':
            telegram_id = params.get('telegramId', [''])[0]
            if not telegram_id:
                return self.send_json(400, {'ok': False, 'error': 'Telegram ID kerak'})
            words = Database.get_words(telegram_id)
            return self.send_json(200, {'ok': True, 'words': words})

        elif path == '/api/stats':
            return self.send_json(200, Database.get_stats())

        else:
            rel = path.lstrip('/') or 'index.html'
            target = os.path.join(PUBLIC_DIR, rel)
            self.send_file_response(target)

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            body = json.loads(post_data.decode('utf-8'))
        except Exception:
            body = {}

        if self.path == '/api/check-auth':
            telegram_id = body.get('telegramId')
            if not telegram_id:
                return self.send_json(200, {'ok': False, 'isSubscribed': False, 'reason': 'no_id', 'message': 'Telegram orqali kirish talab qilinadi.'})
            user = Database.get_user(telegram_id)
            is_sub = Database.is_subscribed(telegram_id)
            days_left = Database.get_remaining_days(telegram_id)
            return self.send_json(200, {
                'ok': True,
                'isSubscribed': is_sub,
                'daysLeft': days_left,
                'user': {
                    'id': user['id'],
                    'firstName': user.get('firstName', ''),
                    'username': user.get('username', ''),
                    'expiresAt': user.get('subscriptionExpiresAt', 0)
                } if user else None
            })

        elif self.path == '/api/save-words':
            telegram_id = body.get('telegramId')
            words = body.get('words', [])
            if not telegram_id or not isinstance(words, list):
                return self.send_json(400, {'ok': False, 'error': "Ma'lumot noto'g'ri"})
            if not Database.is_subscribed(telegram_id):
                return self.send_json(403, {'ok': False, 'error': "Obunangiz faol emas"})
            Database.save_words(telegram_id, words)
            return self.send_json(200, {'ok': True, 'count': len(words)})

        else:
            self.send_json(404, {'error': 'Endpoint topilmadi'})

admin_states = {}

class TelegramBotClient:
    def __init__(self, token):
        self.token = token
        self.base_url = f'https://api.telegram.org/bot{token}'
        self.offset = 0

    def get_webapp_button(self, label="🚀 Lug'atni ochish"):
        if WEBAPP_URL.startswith("https://"):
            return [{"text": label, "web_app": {"url": WEBAPP_URL}}]
        else:
            return [{"text": "🌐 Saytni ochish", "url": "https://t.me/Bm_vocab_bot"}]

    def api_call(self, method, payload=None):
        try:
            url = f'{self.base_url}/{method}'
            data = json.dumps(payload or {}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            print(f"Telegram API Error ({method}):", err_body)
            return {'ok': False, 'error': err_body}
        except Exception as e:
            print(f"Telegram API Exception ({method}):", e)
            return {'ok': False, 'error': str(e)}

    def send_message(self, chat_id, text, reply_markup=None, parse_mode='HTML'):
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup:
            payload['reply_markup'] = reply_markup
        return self.api_call('sendMessage', payload)

    def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode='HTML'):
        payload = {'chat_id': chat_id, 'photo': photo, 'parse_mode': parse_mode}
        if caption:
            payload['caption'] = caption
        if reply_markup:
            payload['reply_markup'] = reply_markup
        return self.api_call('sendPhoto', payload)

    def answer_callback_query(self, callback_query_id, text='', show_alert=False):
        return self.api_call('answerCallbackQuery', {'callback_query_id': callback_query_id, 'text': text, 'show_alert': show_alert})

    def edit_message_caption(self, chat_id, message_id, caption, reply_markup=None, parse_mode='HTML'):
        payload = {'chat_id': chat_id, 'message_id': message_id, 'caption': caption, 'parse_mode': parse_mode}
        if reply_markup:
            payload['reply_markup'] = reply_markup
        return self.api_call('editMessageCaption', payload)

    def get_updates(self):
        try:
            url = f'{self.base_url}/getUpdates'
            data = json.dumps({'offset': self.offset, 'timeout': 15}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=25) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if res.get('ok'):
                    return res.get('result', [])
        except Exception:
            pass
        return []

    def start_polling(self):
        print('Telegram Bot Polling ishga tushdi...')
        while True:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.offset = update['update_id'] + 1
                    self.handle_update(update)
            except Exception as e:
                print('Bot polling loop error:', e)
                time.sleep(2)
            time.sleep(0.3)

    def handle_update(self, update):
        global admin_states
        clean_card = CARD_NUMBER.replace(' ', '')
        click_smart_url = f"{WEBAPP_URL}/pay/click" if WEBAPP_URL.startswith("http") else f"https://my.click.uz/services/p2p?card_num={clean_card}&amount=50000"
        payme_smart_url = f"{WEBAPP_URL}/pay/payme" if WEBAPP_URL.startswith("http") else f"https://payme.uz/{clean_card}/50000"

        if 'callback_query' in update:
            cb = update['callback_query']
            cb_id = cb['id']
            data = cb.get('data', '')
            from_user = cb['from']
            from_id = str(from_user['id'])

            if ADMIN_ID and from_id != ADMIN_ID:
                return self.answer_callback_query(cb_id, 'Faqat admin boshqara oladi!', show_alert=True)

            if data.startswith('approve_'):
                parts = data.split('_')
                target_user_id = parts[1]
                days = int(parts[2]) if len(parts) > 2 else 30
                amount = int(parts[3]) if len(parts) > 3 else 50000
                res = Database.add_subscription(target_user_id, days=days, amount=amount, granted_by='admin_button')
                self.answer_callback_query(cb_id, f'✅ {days} kunlik obuna berildi!')
                msg = cb.get('message', {})
                orig_caption = msg.get('caption', '')
                self.edit_message_caption(chat_id=msg['chat']['id'], message_id=msg['message_id'], caption=f'{orig_caption}\n\n<b>✅ TASDIQLANDI:</b> {days} kunlik ruxsat va sayt linki yuborildi!')
                congrats = (
                    f"🎉 <b>TABRIKLAYMIZ! TO'LOVINGIZ TASDIQLANDI!</b>\n\n"
                    f"Sizga <b>Vocab 3X Pro</b> platformasidan <b>{days} kunlik</b> to'liq foydalanish ruxsati ochildi! 🚀\n"
                    f"⏳ Qolgan muddat: <b>{res['daysLeft']} kun</b>\n\n"
                    f"👇 <b>Saytga kirish uchun quyidagi tugmani bosing:</b>"
                )
                self.send_message(chat_id=target_user_id, text=congrats, reply_markup={'inline_keyboard': [self.get_webapp_button("🚀 Vocab 3X Platformasiga Kirish")]})

            elif data.startswith('reject_'):
                parts = data.split('_')
                target_user_id = parts[1]
                self.answer_callback_query(cb_id, '❌ Rad etildi')
                msg = cb.get('message', {})
                orig_caption = msg.get('caption', '')
                self.edit_message_caption(chat_id=msg['chat']['id'], message_id=msg['message_id'], caption=f'{orig_caption}\n\n<b>❌ RAD ETILDI</b>')
                self.send_message(chat_id=target_user_id, text="❌ <b>To'lov chekingiz tasdiqlanmadi.</b>\nIltimos, to'lov ma'lumotlarini tekshirib adminga murojaat qiling.")

            elif data == 'cmd_add_user':
                self.answer_callback_query(cb_id)
                admin_states[from_id] = 'awaiting_add_user'
                prompt_text = (
                    "➕ <b>HISOB (O'QUVCHI) QO'SHISH:</b>\n\n"
                    "O'quvchining <b>@username</b> yoki <b>Telegram ID raqami</b>ni yuboring:\n\n"
                    "<i>Masalan:</i>\n"
                    "• <code>@shermatov</code>\n"
                    "• <code>123456789</code>\n"
                    "• <code>@shermatov 30</code> (30 kunlik)\n"
                    "• <code>123456789 60</code> (60 kunlik)"
                )
                self.send_message(chat_id=from_id, text=prompt_text)

            elif data == 'cmd_remove_user':
                self.answer_callback_query(cb_id)
                admin_states[from_id] = 'awaiting_remove_user'
                prompt_text = (
                    "➖ <b>OBUNANI BEKOR QILISH:</b>\n\n"
                    "Obunasini to'xtatmoqchi bo'lgan o'quvchining <b>@username</b> yoki <b>Telegram ID</b>sini yuboring:\n\n"
                    "<i>Masalan:</i>\n"
                    "• <code>@shermatov</code>\n"
                    "• <code>123456789</code>"
                )
                self.send_message(chat_id=from_id, text=prompt_text)

            elif data == 'cmd_users':
                self.answer_callback_query(cb_id)
                users = Database.get_all_users()
                if not users:
                    self.send_message(chat_id=from_id, text="Hozircha hech qanday foydalanuvchi yo'q.")
                else:
                    lines = [f"📋 <b>FOYDALANUVCHILAR RO'YXATI ({len(users)} ta):</b>\n"]
                    for idx, u in enumerate(users):
                        status = f"🟢 {u['daysLeft']} kun faol" if u['isActive'] else "🔴 Tugagan"
                        name = u.get('firstName') or u.get('username') or "O'quvchi"
                        lines.append(f"{idx + 1}. {name} ({u.get('username') or 'yoq'}) [<code>{u['id']}</code>] — {status}")
                    self.send_message(chat_id=from_id, text='\n'.join(lines))

            elif data == 'cmd_stats':
                self.answer_callback_query(cb_id)
                stats = Database.get_stats()
                st_text = (
                    f"📊 <b>BATAFSIL STATISTIKA:</b>\n\n"
                    f"👥 Jami foydalanuvchilar: <b>{stats['totalUsers']} ta</b>\n"
                    f"🟢 Faol obunachilar: <b>{stats['activeCount']} ta</b>\n"
                    f"🔴 Muddati tugaganlar: <b>{stats['expiredCount']} ta</b>\n"
                    f"💰 Jami tushum: <b>{stats['totalRevenue']:,} so'm</b>\n"
                    f"✅ Tasdiqlangan to'lovlar: <b>{stats.get('approvedPayments', 0)} ta</b>"
                )
                self.send_message(chat_id=from_id, text=st_text)

            elif data == 'show_card':
                self.answer_callback_query(cb_id)
                card_msg = (
                    f"💳 <b>TO'LOV KARTASI:</b>\n\n"
                    f"<code>{clean_card}</code>\n\n"
                    f"💎 <b>Oylik to'lov:</b> {PRICE_UZS} so'm\n\n"
                    f"📲 <i>Click yoki Payme ilovangiz orqali 50 000 so'm o'tkazib, chek rasmini shu botga yuboring.</i>"
                )
                self.send_message(chat_id=from_id, text=card_msg)
            return

        if 'message' in update:
            msg = update['message']
            chat_id = msg['chat']['id']
            from_user = msg.get('from', {})
            user_id = str(from_user.get('id'))
            text = (msg.get('text') or '').strip()
            text_lower = text.lower()
            Database.register_or_update_user(user_id, {'username': from_user.get('username', ''), 'firstName': from_user.get('first_name', ''), 'lastName': from_user.get('last_name', '')})

            # Check for receipt photo upload
            if 'photo' in msg:
                photo_id = msg['photo'][-1]['file_id']
                self.send_message(chat_id=chat_id, text="✅ <b>Chekingiz qabul qilindi!</b>\n\nAdmin to'lovni tekshirib tasdiqlashi bilan sizga <b>platformaga kirish havolasi</b> ochiladi ⏳")
                if ADMIN_ID:
                    caption = (
                        f"🔔 <b>YANGI TO'LOV CHEKI KELDI!</b>\n\n"
                        f"👤 <b>O'quvchi:</b> {from_user.get('first_name', '')} {from_user.get('last_name', '')}\n"
                        f"🔗 <b>Username:</b> @{from_user.get('username', 'yoq')}\n"
                        f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
                        f"💰 <b>To'lov summasi:</b> {PRICE_UZS} so'm\n"
                        f"📅 <b>Vaqt:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"Ushbu to'lovni tasdiqlab, o'quvchiga sayt linkini yuborasizmi?"
                    )
                    self.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption, reply_markup={'inline_keyboard': [
                        [{'text': f'✅ Tasdiqlash va Link yuborish ({PRICE_UZS} so\'m)', 'callback_data': f'approve_{user_id}_30_50000'}],
                        [{'text': '❌ Rad etish', 'callback_data': f'reject_{user_id}'}]
                    ]})
                return

            # --- ADMIN HANDLERS ---
            if ADMIN_ID and user_id == ADMIN_ID:
                # If admin is in awaiting_add_user state
                if admin_states.get(user_id) == 'awaiting_add_user':
                    admin_states.pop(user_id, None)
                    parts = text.split()
                    if parts:
                        target = parts[0]
                        days = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 30
                        user_obj = Database.find_user(target)
                        target_id = user_obj['id'] if user_obj else (None if target.startswith('@') else target)
                        if not target_id:
                            return self.send_message(chat_id=chat_id, text=f"❌ <code>{target}</code> topilmadi. Foydalanuvchi botga avval kamida bir marta /start bosgan bo'lishi kerak yoki to'g'ri Telegram ID kiriting.")
                        res = Database.add_subscription(target_id, days=days, amount=50000, granted_by='admin_interactive')
                        target_name = f"@{user_obj.get('username')}" if user_obj and user_obj.get('username') else target_id
                        self.send_message(chat_id=chat_id, text=f"✅ <b>Hisob faollashtirildi!</b>\nFoydalanuvchi: <code>{target_name}</code> (ID: <code>{target_id}</code>)\nObuna: <b>{days} kun</b>\nQolgan muddat: <b>{res['daysLeft']} kun</b>.")
                        try:
                            self.send_message(chat_id=target_id, text=f"🎉 <b>Admin sizning hisobingizga {days} kunlik obuna qo'shdi!</b>\nPlatformadan bemalol foydalanishingiz mumkin 👇", reply_markup={'inline_keyboard': [self.get_webapp_button("🚀 Vocab 3X Platformasiga Kirish")]})
                        except Exception:
                            pass
                        return

                # If admin is in awaiting_remove_user state
                if admin_states.get(user_id) == 'awaiting_remove_user':
                    admin_states.pop(user_id, None)
                    parts = text.split()
                    if parts:
                        target = parts[0]
                        user_obj = Database.find_user(target)
                        target_id = user_obj['id'] if user_obj else target
                        if Database.remove_subscription(target_id):
                            target_name = f"@{user_obj.get('username')}" if user_obj and user_obj.get('username') else target_id
                            self.send_message(chat_id=chat_id, text=f"⛔ <b>Obuna bekor qilindi!</b>\nFoydalanuvchi: <code>{target_name}</code> (ID: <code>{target_id}</code>)")
                            try:
                                self.send_message(chat_id=target_id, text="⚠️ Sizning platformadagi obunangiz admin tomonidan to'xtatildi.")
                            except Exception:
                                pass
                        else:
                            self.send_message(chat_id=chat_id, text=f"❌ <code>{target}</code> topilmadi.")
                        return

                if text.startswith('/start') or text_lower in ['start', '/admin', 'admin', 'panel']:
                    stats = Database.get_stats()
                    admin_text = (
                        f"👑 <b>ASSALOMU ALAYKUM, HURMATLI ADMIN (@{ADMIN_USERNAME})!</b>\n\n"
                        f"Vocab 3X Pro boshqaruv markaziga xush kelibsiz.\n\n"
                        f"💳 <b>To'lov kartasi:</b> <code>{clean_card}</code>\n"
                        f"💎 <b>Oylik obuna narxi:</b> {PRICE_UZS} so'm\n\n"
                        f"📊 <b>Statistika:</b>\n"
                        f"• 👥 Jami o'quvchilar: <b>{stats['totalUsers']} ta</b>\n"
                        f"• 🟢 Faol obunachilar: <b>{stats['activeCount']} ta</b>\n"
                        f"• 🔴 Muddati tugaganlar: <b>{stats['expiredCount']} ta</b>\n"
                        f"• 💰 Jami tushum: <b>{stats['totalRevenue']:,} so'm</b>\n\n"
                        f"⚡ <b>Buyruqlar:</b>\n"
                        f"• <code>/add @username 30</code> yoki <code>/add 12345678 30</code> — Obuna qo'shish\n"
                        f"• <code>/remove @username</code> yoki <code>/remove 12345678</code> — Obunani bekor qilish\n"
                        f"• <code>/users</code> — Foydalanuvchilar ro'yxati\n"
                        f"• <code>/broadcast Matn</code> — Barcha o'quvchilarga xabar"
                    )
                    buttons = [
                        self.get_webapp_button("🚀 Platformani ochish (Admin kirishi)"),
                        [
                            {'text': '➕ Obuna berish', 'callback_data': 'cmd_add_user'},
                            {'text': '➖ Bekor qilish', 'callback_data': 'cmd_remove_user'}
                        ],
                        [{'text': '👥 Foydalanuvchilar', 'callback_data': 'cmd_users'}, {'text': '📊 Statistika', 'callback_data': 'cmd_stats'}]
                    ]
                    return self.send_message(chat_id=chat_id, text=admin_text, reply_markup={'inline_keyboard': buttons})

                if text.startswith('/add') or text.startswith('/qosh') or text.startswith('/qoshish'):
                    parts = text.split()
                    if len(parts) >= 2:
                        target = parts[1]
                        days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 30
                        user_obj = Database.find_user(target)
                        target_id = user_obj['id'] if user_obj else (None if target.startswith('@') else target)
                        if not target_id:
                            return self.send_message(chat_id=chat_id, text=f"❌ <code>{target}</code> topilmadi. Foydalanuvchi botga avval kamida bir marta /start bosgan bo'lishi kerak yoki to'g'ridan-to'g'ri Telegram ID raqamini yozing.")
                        res = Database.add_subscription(target_id, days=days, amount=50000, granted_by='admin_manual')
                        target_name = f"@{user_obj.get('username')}" if user_obj and user_obj.get('username') else target_id
                        self.send_message(chat_id=chat_id, text=f"✅ <code>{target_name}</code> (ID: <code>{target_id}</code>) ga <b>{days} kunlik</b> obuna berildi! Qolgan muddat: {res['daysLeft']} kun.")
                        try:
                            self.send_message(chat_id=target_id, text=f"🎉 <b>Admin sizga {days} kunlik obuna taqdim etdi!</b>\nPlatformadan bemalol foydalanishingiz mumkin 👇", reply_markup={'inline_keyboard': [self.get_webapp_button("🚀 Vocab 3X Platformasiga Kirish")]})
                        except Exception:
                            pass
                        return
                    else:
                        admin_states[user_id] = 'awaiting_add_user'
                        return self.send_message(chat_id=chat_id, text="➕ O'quvchining <b>@username</b> yoki <b>Telegram ID</b>sini yuboring (masalan: <code>@shermatov 30</code>):")

                if text.startswith('/remove') or text.startswith('/ochir') or text.startswith('/bekor'):
                    parts = text.split()
                    if len(parts) >= 2:
                        target = parts[1]
                        user_obj = Database.find_user(target)
                        target_id = user_obj['id'] if user_obj else target
                        if Database.remove_subscription(target_id):
                            target_name = f"@{user_obj.get('username')}" if user_obj and user_obj.get('username') else target_id
                            self.send_message(chat_id=chat_id, text=f"⛔ <code>{target_name}</code> (ID: <code>{target_id}</code>) ning obunasi to'xtatildi.")
                            try:
                                self.send_message(chat_id=target_id, text="⚠️ Sizning platformadagi obunangiz to'xtatildi.")
                            except Exception:
                                pass
                        else:
                            self.send_message(chat_id=chat_id, text=f"❌ <code>{target}</code> topilmadi.")
                        return
                    else:
                        admin_states[user_id] = 'awaiting_remove_user'
                        return self.send_message(chat_id=chat_id, text="➖ Obunani bekor qilish uchun o'quvchining <b>@username</b> yoki <b>Telegram ID</b>sini yuboring (masalan: <code>@shermatov</code>):")

                if text == '/users' or text_lower == 'users':
                    users = Database.get_all_users()
                    if not users:
                        return self.send_message(chat_id=chat_id, text="Hozircha hech qanday foydalanuvchi yo'q.")
                    lines = [f"📋 <b>FOYDALANUVCHILAR RO'YXATI ({len(users)} ta):</b>\n"]
                    for idx, u in enumerate(users):
                        status = f"🟢 {u['daysLeft']} kun faol" if u['isActive'] else "🔴 Tugagan"
                        name = u.get('firstName') or u.get('username') or "O'quvchi"
                        lines.append(f"{idx + 1}. {name} ({u.get('username') or 'yoq'}) [<code>{u['id']}</code>] — {status}")
                    return self.send_message(chat_id=chat_id, text='\n'.join(lines))

                if text.startswith('/broadcast'):
                    broadcast_msg = text.replace('/broadcast', '', 1).strip()
                    if broadcast_msg:
                        users = Database.get_all_users()
                        sent_count = 0
                        for u in users:
                            if u['id'] != ADMIN_ID:
                                try:
                                    self.send_message(chat_id=u['id'], text=f"📢 <b>XABAR:</b>\n\n{broadcast_msg}")
                                    sent_count += 1
                                except Exception:
                                    pass
                        self.send_message(chat_id=chat_id, text=f"🚀 Xabar {sent_count} ta o'quvchiga yuborildi!")
                        return

            # --- USER (STUDENT) HANDLERS ---
            if text.startswith('/start') or text_lower == 'start':
                is_sub = Database.is_subscribed(user_id)
                days_left = Database.get_remaining_days(user_id)
                if is_sub:
                    welcome_text = (
                        f"Assalomu alaykum, <b>{from_user.get('first_name', '')}</b>! 🎉\n\n"
                        f"Sizning <b>Vocab 3X Pro</b> obunangiz faol holatda!\n"
                        f"⏳ Qolgan muddat: <b>{days_left} kun</b>\n\n"
                        f"O'z so'zlaringiz ustida mashq qilish uchun pastdagi tugmani bosing 👇"
                    )
                    return self.send_message(chat_id=chat_id, text=welcome_text, reply_markup={'inline_keyboard': [self.get_webapp_button("🚀 Vocab 3X Saytini ochish")]})
                
                # Payment presentation for non-subscribed students
                offer_text = (
                    f"Assalomu alaykum, <b>{from_user.get('first_name', '')}</b>! 🇬🇧\n\n"
                    f"<b>Vocab 3X Pro</b> — ingliz tili so'zlarini Flashcard, Tezkor test, Juftlik o'yini va Yozish mashqlari orqali 3 barobar tezroq yodlash platformasi.\n\n"
                    f"🔒 <b>PLATFORMAGA KIRISH TO'LOV ASOSIDA:</b>\n"
                    f"💎 <b>Oylik obuna narxi:</b> <b>{PRICE_UZS} so'm</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💳 <b>TO'LOV KARTASI:</b> (ustiga bosing - nusxalanadi)\n"
                    f"<code>{clean_card}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📲 <b>To'lov usuli:</b>\n"
                    f"Pastdagi <b>🟢 Click</b> yoki <b>🔵 Payme</b> tugmasini bossangiz, to'g'ridan-to'g'ri ilovaga kirib <b>50 000 so'm</b> to'lov sahifasi ochiladi.\n\n"
                    f"📸 <b>QANDAY FAOLLASHTIRILADI?</b>\n"
                    f"1️⃣ Click yoki Payme orqali <b>{PRICE_UZS} so'm</b> to'lov qiling.\n"
                    f"2️⃣ To'lov chekini (skrinshotini) <b>shu yerga rasm ko'rinishida yuboring</b>.\n"
                    f"3️⃣ Admin to'lovni tasdiqlashi bilan sizga <b>saytga kirish linki</b> yuboriladi!"
                )
                buttons = [
                    [
                        {'text': '🟢 Click ilovasida to\'lash', 'url': click_smart_url},
                        {'text': '🔵 Payme ilovasida to\'lash', 'url': payme_smart_url}
                    ],
                    [
                        {'text': '🤖 @clickuz bot orqali to\'lash', 'url': 'https://t.me/clickuz'}
                    ],
                    [{'text': '📋 Karta raqamini ko\'rish', 'callback_data': 'show_card'}],
                    [{'text': '👨‍💻 Adminga savol berish', 'url': f'https://t.me/{ADMIN_USERNAME}'}]
                ]
                return self.send_message(chat_id=chat_id, text=offer_text, reply_markup={'inline_keyboard': buttons})

def start_bot_thread():
    if BOT_TOKEN and BOT_TOKEN != 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
        bot_client = TelegramBotClient(BOT_TOKEN)
        t = threading.Thread(target=bot_client.start_polling, daemon=True)
        t.start()
    else:
        print('⚠️ BOT_TOKEN sozlanmagan. Bot ishlamaydi. Iltimos, .env faylini to''ldiring.')

if __name__ == '__main__':
    start_bot_thread()
    print('='*50)
    print('🚀 Vocab 3X Pro Server ishga tushmoqda!')
    print(f'🌐 Veb-sayt: http://localhost:{PORT}')
    print(f'📱 Mini App URL: {WEBAPP_URL}')
    print('='*50)
    httpd = ThreadingHTTPServer(('0.0.0.0', PORT), VocabHTTPHandler)
    httpd.serve_forever()

