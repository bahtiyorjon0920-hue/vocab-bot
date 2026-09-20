import os
import sys
import json
import time
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
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'BM_visual').strip().replace('@', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', f'http://localhost:{PORT}').strip()
CARD_NUMBER = os.getenv('CARD_NUMBER', '5614 6820 5096 7480').strip()
PRICE_UZS = os.getenv('PRICE_PER_MONTH', '50 000').strip()
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')

class VocabHTTPHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Session-Token')

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

    def send_html(self, status, html_content):
        body = html_content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
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

    def get_auth_user(self, body=None, params=None):
        token = self.headers.get('X-Session-Token') or self.headers.get('Authorization', '').replace('Bearer ', '').strip()
        if not token and body and isinstance(body, dict):
            token = body.get('token')
        if not token and params:
            token = params.get('token', [''])[0]
        if not token:
            return None
        return Database.get_user_by_token(token)

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
  <title>Click orqali to'lov</title>
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
        <span class="info-val">{PRICE_UZS} so'm</span>
      </div>
      <div>
        <span class="info-label" style="font-size: 13px;">Karta raqami (bosib nusxalang):</span>
        <div class="card-num" onclick="copyCard()">
          <span>{clean_card}</span>
          <span style="font-size: 12px; background: #38bdf8; color: #000; padding: 2px 8px; border-radius: 6px;">Nusxalash 📋</span>
        </div>
      </div>
    </div>
    <a href="intent://my.click.uz/services/p2p?card_num={clean_card}&amount=50000#Intent;package=uz.click.app;scheme=https;end;" class="btn btn-main">📲 Click ilovasida ochish</a>
    <a href="https://my.click.uz/services/p2p?card_num={clean_card}&amount=50000" class="btn btn-sub">🌐 Brauzerda ochish</a>
  </div>
  <script>
    function copyCard() {{
      if (navigator.clipboard) navigator.clipboard.writeText('{clean_card}');
      const t = document.getElementById('toast');
      t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 3000);
    }}
    window.addEventListener('DOMContentLoaded', () => {{
      const isAndroid = /Android/i.test(navigator.userAgent);
      const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
      if (isAndroid) {{
        window.location.href = "intent://my.click.uz/services/p2p?card_num={clean_card}&amount=50000#Intent;package=uz.click.app;scheme=https;end;";
      }} else if (isIOS) {{
        window.location.href = "click://pay/p2p?card={clean_card}&amount=50000";
        setTimeout(() => {{ window.location.href = "https://my.click.uz/services/p2p?card_num={clean_card}&amount=50000"; }}, 1500);
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
  <title>Payme orqali to'lov</title>
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
        <span class="info-val">{PRICE_UZS} so'm</span>
      </div>
      <div>
        <span class="info-label" style="font-size: 13px;">Karta raqami (bosib nusxalang):</span>
        <div class="card-num" onclick="copyCard()">
          <span>{clean_card}</span>
          <span style="font-size: 12px; background: #38bdf8; color: #000; padding: 2px 8px; border-radius: 6px;">Nusxalash 📋</span>
        </div>
      </div>
    </div>
    <a href="intent://payme.uz/{clean_card}/50000#Intent;package=uz.dida.payme;scheme=https;end;" class="btn btn-main">📲 Payme ilovasida ochish</a>
    <a href="https://payme.uz/{clean_card}/50000" class="btn btn-sub">🌐 Brauzerda ochish</a>
  </div>
  <script>
    function copyCard() {{
      if (navigator.clipboard) navigator.clipboard.writeText('{clean_card}');
      const t = document.getElementById('toast');
      t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 3000);
    }}
    window.addEventListener('DOMContentLoaded', () => {{
      const isAndroid = /Android/i.test(navigator.userAgent);
      const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
      if (isAndroid) {{
        window.location.href = "intent://payme.uz/{clean_card}/50000#Intent;package=uz.dida.payme;scheme=https;end;";
      }} else if (isIOS) {{
        window.location.href = "payme://transfer?card={clean_card}&amount=50000";
        setTimeout(() => {{ window.location.href = "https://payme.uz/{clean_card}/50000"; }}, 1500);
      }}
    }});
  </script>
</body>
</html>"""
            return self.send_html(200, html)

        elif path == '/api/me':
            user = self.get_auth_user(params=params)
            if not user:
                return self.send_json(401, {'ok': False, 'error': 'Tizimga kiring'})
            is_sub = Database.is_subscribed(user['id'])
            days_left = Database.get_remaining_days(user['id'])
            return self.send_json(200, {
                'ok': True,
                'user': {
                    'id': user['id'],
                    'email': user.get('email', ''),
                    'username': user.get('username', ''),
                    'fullName': user.get('fullName', ''),
                    'role': user.get('role', 'student'),
                    'isSubscribed': is_sub,
                    'daysLeft': days_left,
                    'receiptStatus': user.get('receiptStatus', 'none')
                }
            })

        elif path == '/api/get-words':
            user = self.get_auth_user(params=params)
            if not user:
                return self.send_json(401, {'ok': False, 'error': 'Tizimga kiring'})
            words = Database.get_words(user['id'])
            return self.send_json(200, {'ok': True, 'words': words})

        elif path == '/api/admin/stats':
            user = self.get_auth_user(params=params)
            if not user or user.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            stats = Database.get_stats()
            return self.send_json(200, {'ok': True, 'stats': stats})

        elif path == '/api/admin/users':
            user = self.get_auth_user(params=params)
            if not user or user.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            users = Database.get_all_users()
            return self.send_json(200, {'ok': True, 'users': users})

        elif path == '/api/admin/receipts':
            user = self.get_auth_user(params=params)
            if not user or user.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            receipts = Database.get_pending_receipts()
            return self.send_json(200, {'ok': True, 'receipts': receipts})

        elif path in ('/admin', '/admin/'):
            target = os.path.join(PUBLIC_DIR, 'admin.html')
            return self.send_file_response(target)

        elif path == '/api/admin/admins-list':
            user = self.get_auth_user(params=params)
            if not user or user.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            admins = Database.get_admins()
            return self.send_json(200, {'ok': True, 'admins': admins})

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

        if self.path == '/api/register':
            username = body.get('username', '').strip().replace('@', '')
            password = body.get('password', '').strip()
            full_name = body.get('fullName', '').strip() or username
            email = body.get('email', '').strip().lower() or f"{username}@vocab.uz"

            if not username or not password:
                return self.send_json(400, {'ok': False, 'error': "Username va parol kiritilishi shart!"})
            if len(password) < 4:
                return self.send_json(400, {'ok': False, 'error': "Parol kamida 4 ta belgidan iborat bo'lsin!"})
            if len(username) < 3:
                return self.send_json(400, {'ok': False, 'error': "Username kamida 3 ta belgidan iborat bo'lsin!"})

            res = Database.register_user(email, username, password, full_name)
            if not res['ok']:
                return self.send_json(400, res)

            u = res['user']
            is_sub = Database.is_subscribed(u['id'])
            days_left = Database.get_remaining_days(u['id'])

            return self.send_json(200, {
                'ok': True,
                'token': res['token'],
                'user': {
                    'id': u['id'],
                    'email': u['email'],
                    'username': u['username'],
                    'fullName': u['fullName'],
                    'role': u['role'],
                    'isSubscribed': is_sub,
                    'daysLeft': days_left,
                    'receiptStatus': u.get('receiptStatus', 'none')
                }
            })

        elif self.path == '/api/login':
            login_query = body.get('login', '') or body.get('username', '') or body.get('email', '')
            password = body.get('password', '')

            if not login_query or not password:
                return self.send_json(400, {'ok': False, 'error': 'Login va parol kiritilishi shart!'})

            res = Database.authenticate(login_query, password)
            if not res['ok']:
                return self.send_json(400, res)

            u = res['user']
            is_sub = Database.is_subscribed(u['id'])
            days_left = Database.get_remaining_days(u['id'])

            return self.send_json(200, {
                'ok': True,
                'token': res['token'],
                'user': {
                    'id': u['id'],
                    'email': u['email'],
                    'username': u['username'],
                    'fullName': u['fullName'],
                    'role': u['role'],
                    'isSubscribed': is_sub,
                    'daysLeft': days_left,
                    'receiptStatus': u.get('receiptStatus', 'none')
                }
            })

        elif self.path == '/api/logout':
            token = self.headers.get('X-Session-Token') or body.get('token')
            if token:
                Database.delete_session(token)
            return self.send_json(200, {'ok': True})

        elif self.path == '/api/submit-receipt':
            user = self.get_auth_user(body=body)
            if not user:
                return self.send_json(401, {'ok': False, 'error': 'Tizimga kiring'})
            image_data = body.get('image', '')
            if not image_data:
                return self.send_json(400, {'ok': False, 'error': 'Chek rasmi yuklanmadi'})
            res = Database.submit_receipt(user['id'], image_data)
            return self.send_json(200, res)

        elif self.path == '/api/save-words':
            user = self.get_auth_user(body=body)
            if not user:
                return self.send_json(401, {'ok': False, 'error': 'Tizimga kiring'})
            if not Database.is_subscribed(user['id']):
                return self.send_json(403, {'ok': False, 'error': 'Obunangiz faol emas'})
            words = body.get('words', [])
            Database.save_words(user['id'], words)
            return self.send_json(200, {'ok': True, 'count': len(words)})

        # --- ADMIN POST ENDPOINTS ---
        elif self.path == '/api/admin/approve-receipt':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            receipt_id = body.get('receiptId')
            days = int(body.get('days', 30))
            res = Database.approve_receipt(receipt_id, days=days)
            return self.send_json(200, res)

        elif self.path == '/api/admin/reject-receipt':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            receipt_id = body.get('receiptId')
            res = Database.reject_receipt(receipt_id)
            return self.send_json(200, res)

        elif self.path == '/api/admin/grant-sub':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            target = body.get('target', '')
            days = int(body.get('days', 30))
            res = Database.add_subscription(target, days=days)
            return self.send_json(200, res)

        elif self.path == '/api/admin/create-user':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            username = body.get('username', '').strip().replace('@', '')
            password = body.get('password', '123456').strip()
            full_name = body.get('fullName', '').strip() or username
            email = body.get('email', '').strip().lower() or f"{username}@vocab.uz"
            days = int(body.get('days', 30))

            if not username or not password:
                return self.send_json(400, {'ok': False, 'error': 'Username va parol kiritilishi shart!'})
            res = Database.register_user(email, username, password, full_name)
            if not res['ok']:
                return self.send_json(400, res)
            u = res['user']
            if days > 0:
                Database.add_subscription(u['id'], days=days)
            return self.send_json(200, {'ok': True, 'user': u, 'message': 'Yangi o\'quvchi muvaffaqiyatli qo\'shildi!'})

        elif self.path == '/api/admin/revoke-sub':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            target = body.get('target', '')
            res = Database.remove_subscription(target)
            return self.send_json(200, res)

        elif self.path == '/api/admin/create-admin':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            username = body.get('username', '').strip().replace('@', '')
            password = body.get('password', '').strip()
            full_name = body.get('fullName', '').strip() or username
            email = body.get('email', '').strip().lower() or f"{username}@admin.vocab.uz"

            if not username or not password:
                return self.send_json(400, {'ok': False, 'error': 'Admin username va parol kiritilishi shart!'})
            res = Database.create_admin(email, username, password, full_name)
            return self.send_json(200 if res['ok'] else 400, res)

        elif self.path == '/api/admin/promote-user':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            target = body.get('target', '')
            res = Database.promote_to_admin(target)
            return self.send_json(200 if res['ok'] else 400, res)

        elif self.path == '/api/admin/demote-user':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            target = body.get('target', '')
            res = Database.demote_from_admin(target)
            return self.send_json(200 if res['ok'] else 400, res)

        elif self.path == '/api/admin/kick-user' or self.path == '/api/admin/delete-user':
            admin = self.get_auth_user(body=body)
            if not admin or admin.get('role') != 'admin':
                return self.send_json(403, {'ok': False, 'error': 'Ruxsat berilmagan'})
            target = body.get('target', '')
            res = Database.kick_user(target)
            return self.send_json(200 if res['ok'] else 400, res)

        else:
            self.send_json(404, {'error': 'Endpoint topilmadi'})

if __name__ == '__main__':
    print('='*50)
    print('🚀 Vocab 3X Pro Standalone Web Server ishga tushmoqda!')
    print(f'🌐 Veb-sayt: http://localhost:{PORT}')
    print(f'👑 Standart Admin Login: BM_visual | Parol: admin123')
    print('='*50)
    httpd = ThreadingHTTPServer(('0.0.0.0', PORT), VocabHTTPHandler)
    httpd.serve_forever()
