import os
import json
import time
import hashlib
import uuid

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_FILE = os.path.join(DATA_DIR, 'database.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

def hash_password(password, salt='vocab_salt_2026'):
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def load_db():
    if not os.path.exists(DB_FILE):
        admin_pass = hash_password('admin123')
        initial = {
            'users': {
                'admin_bm': {
                    'id': 'admin_bm',
                    'email': 'bm_visual@vocab.uz',
                    'username': 'BM_visual',
                    'fullName': 'Admin BM Visual',
                    'passwordHash': admin_pass,
                    'role': 'admin',
                    'joinedAt': int(time.time() * 1000),
                    'subscriptionExpiresAt': 9999999999999,
                    'subscriptionHistory': [],
                    'receiptStatus': 'approved',
                    'words': []
                }
            },
            'receipts': {},
            'sessions': {},
            'stats': {
                'totalRevenue': 0,
                'approvedPayments': 0
            }
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial, f, indent=2, ensure_ascii=False)
        return initial
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'receipts' not in data: data['receipts'] = {}
            if 'sessions' not in data: data['sessions'] = {}
            if 'stats' not in data: data['stats'] = {'totalRevenue': 0, 'approvedPayments': 0}
            
            # Ensure BM_visual admin exists and has valid password
            admin_user = data['users'].get('admin_bm')
            admin_pass = hash_password('admin123')
            if not admin_user:
                data['users']['admin_bm'] = {
                    'id': 'admin_bm',
                    'email': 'bm_visual@vocab.uz',
                    'username': 'BM_visual',
                    'fullName': 'Admin BM Visual',
                    'passwordHash': admin_pass,
                    'role': 'admin',
                    'joinedAt': int(time.time() * 1000),
                    'subscriptionExpiresAt': 9999999999999,
                    'subscriptionHistory': [],
                    'receiptStatus': 'approved',
                    'words': []
                }
                save_db(data)
            elif admin_user.get('passwordHash') != admin_pass:
                admin_user['passwordHash'] = admin_pass
                admin_user['role'] = 'admin'
                admin_user['subscriptionExpiresAt'] = 9999999999999
                save_db(data)
            return data
    except Exception as e:
        print('Database read error:', e)
        return {'users': {}, 'receipts': {}, 'sessions': {}, 'stats': {}}

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print('Database save error:', e)

class Database:
    @staticmethod
    def create_session(user_id):
        data = load_db()
        token = 'tok_' + uuid.uuid4().hex
        data['sessions'][token] = {
            'userId': user_id,
            'createdAt': int(time.time() * 1000)
        }
        save_db(data)
        return token

    @staticmethod
    def get_user_by_token(token):
        if not token:
            return None
        data = load_db()
        sess = data['sessions'].get(token)
        if not sess:
            return None
        user_id = sess.get('userId')
        return data['users'].get(user_id)

    @staticmethod
    def delete_session(token):
        data = load_db()
        if token in data['sessions']:
            del data['sessions'][token]
            save_db(data)
            return True
        return False

    @staticmethod
    def register_user(email, username, password, full_name=''):
        data = load_db()
        email = email.strip().lower()
        username = username.strip().replace('@', '')
        
        # Check uniqueness
        for u in data['users'].values():
            if email and u.get('email', '').lower() == email:
                return {'ok': False, 'error': 'Ushbu Gmail/Email bilan allaqachon ro\'yxatdan o\'tilgan!'}
            if u.get('username', '').lower() == username.lower():
                return {'ok': False, 'error': 'Ushbu Username allaqachon band qilingan!'}

        user_id = 'u_' + uuid.uuid4().hex[:10]
        now_ms = int(time.time() * 1000)
        pass_hash = hash_password(password)

        is_admin = (username.lower() == 'bm_visual' or email == 'bm_visual@vocab.uz')
        role = 'admin' if is_admin else 'student'
        exp = 9999999999999 if is_admin else 0

        new_user = {
            'id': user_id,
            'email': email,
            'username': username,
            'fullName': full_name or username,
            'passwordHash': pass_hash,
            'role': role,
            'joinedAt': now_ms,
            'subscriptionExpiresAt': exp,
            'subscriptionHistory': [],
            'receiptStatus': 'approved' if is_admin else 'none',
            'words': []
        }

        data['users'][user_id] = new_user
        save_db(data)
        token = Database.create_session(user_id)
        return {'ok': True, 'user': new_user, 'token': token}

    @staticmethod
    def authenticate(login_query, password):
        data = load_db()
        raw_q = login_query.strip()
        q_lower = raw_q.lower()
        q_no_at = q_lower.replace('@', '')
        target_user = None

        for u in data['users'].values():
            u_email = u.get('email', '').strip().lower()
            u_user = u.get('username', '').strip().lower()
            u_id = str(u.get('id', '')).strip().lower()
            if u_email == q_lower or u_user == q_lower or u_user == q_no_at or u_id == q_lower:
                target_user = u
                break

        if not target_user:
            return {'ok': False, 'error': 'Bunday foydalanuvchi topilmadi!'}

        pass_hash = hash_password(password)
        if target_user.get('passwordHash') != pass_hash:
            return {'ok': False, 'error': 'Parol noto\'g\'ri kiritildi!'}

        token = Database.create_session(target_user['id'])
        return {'ok': True, 'user': target_user, 'token': token}

    @staticmethod
    def is_subscribed(user_id):
        data = load_db()
        user = data['users'].get(user_id)
        if not user:
            return False
        if user.get('role') == 'admin':
            return True
        now_ms = int(time.time() * 1000)
        return user.get('subscriptionExpiresAt', 0) > now_ms

    @staticmethod
    def get_remaining_days(user_id):
        data = load_db()
        user = data['users'].get(user_id)
        if not user:
            return 0
        if user.get('role') == 'admin':
            return 9999
        now_ms = int(time.time() * 1000)
        exp = user.get('subscriptionExpiresAt', 0)
        if exp <= now_ms:
            return 0
        return max(0, int((exp - now_ms) / (1000 * 60 * 60 * 24))) + 1

    @staticmethod
    def submit_receipt(user_id, receipt_image_data):
        data = load_db()
        user = data['users'].get(user_id)
        if not user:
            return {'ok': False, 'error': 'Foydalanuvchi topilmadi'}

        receipt_id = 'rcpt_' + uuid.uuid4().hex[:8]
        now_ms = int(time.time() * 1000)

        receipt_entry = {
            'id': receipt_id,
            'userId': user_id,
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'fullName': user.get('fullName', ''),
            'image': receipt_image_data,
            'submittedAt': now_ms,
            'status': 'pending',
            'amount': 50000
        }

        data['receipts'][receipt_id] = receipt_entry
        user['receiptStatus'] = 'pending'
        user['lastReceiptId'] = receipt_id
        save_db(data)
        return {'ok': True, 'receiptId': receipt_id}

    @staticmethod
    def get_pending_receipts():
        data = load_db()
        pending = []
        for r in data['receipts'].values():
            if r.get('status') == 'pending':
                pending.append(r)
        pending.sort(key=lambda x: x.get('submittedAt', 0), reverse=True)
        return pending

    @staticmethod
    def approve_receipt(receipt_id, days=30, amount=50000):
        data = load_db()
        receipt = data['receipts'].get(receipt_id)
        if not receipt:
            return {'ok': False, 'error': 'Chek topilmadi'}

        receipt['status'] = 'approved'
        receipt['approvedAt'] = int(time.time() * 1000)

        user_id = receipt['userId']
        res = Database.add_subscription(user_id, days=days, amount=amount, granted_by='receipt_approval')
        
        data = load_db()
        if user_id in data['users']:
            data['users'][user_id]['receiptStatus'] = 'approved'
            save_db(data)

        return {'ok': True, 'daysLeft': res['daysLeft']}

    @staticmethod
    def reject_receipt(receipt_id):
        data = load_db()
        receipt = data['receipts'].get(receipt_id)
        if not receipt:
            return {'ok': False, 'error': 'Chek topilmadi'}

        receipt['status'] = 'rejected'
        receipt['rejectedAt'] = int(time.time() * 1000)

        user_id = receipt['userId']
        if user_id in data['users']:
            data['users'][user_id]['receiptStatus'] = 'rejected'
        save_db(data)
        return {'ok': True}

    @staticmethod
    def add_subscription(user_id_or_query, days=30, amount=50000, granted_by='admin'):
        data = load_db()
        target_user = None
        q = str(user_id_or_query).strip().lower().replace('@', '')

        for u in data['users'].values():
            if str(u.get('id')).lower() == q or u.get('username', '').lower() == q or u.get('email', '').lower() == q:
                target_user = u
                break

        if not target_user:
            return {'ok': False, 'error': 'Foydalanuvchi topilmadi'}

        now_ms = int(time.time() * 1000)
        curr_exp = target_user.get('subscriptionExpiresAt', 0)
        base = curr_exp if curr_exp > now_ms else now_ms
        target_user['subscriptionExpiresAt'] = base + (days * 24 * 60 * 60 * 1000)
        target_user['receiptStatus'] = 'approved'

        if 'subscriptionHistory' not in target_user:
            target_user['subscriptionHistory'] = []
        target_user['subscriptionHistory'].append({
            'date': now_ms,
            'days': days,
            'amount': amount,
            'grantedBy': granted_by,
            'expiresAt': target_user['subscriptionExpiresAt']
        })

        if 'stats' not in data:
            data['stats'] = {'totalRevenue': 0, 'approvedPayments': 0}
        data['stats']['totalRevenue'] = data['stats'].get('totalRevenue', 0) + amount
        data['stats']['approvedPayments'] = data['stats'].get('approvedPayments', 0) + 1

        save_db(data)
        days_left = max(0, int((target_user['subscriptionExpiresAt'] - now_ms) / (1000 * 60 * 60 * 24)))
        return {'ok': True, 'user': target_user, 'daysLeft': days_left}

    @staticmethod
    def remove_subscription(user_id_or_query):
        data = load_db()
        q = str(user_id_or_query).strip().lower().replace('@', '')
        for u in data['users'].values():
            if str(u.get('id')).lower() == q or u.get('username', '').lower() == q or u.get('email', '').lower() == q:
                if u.get('role') == 'admin':
                    return {'ok': False, 'error': 'Admin obunasini to\'xtatib bo\'lmaydi'}
                u['subscriptionExpiresAt'] = 0
                u['receiptStatus'] = 'none'
                save_db(data)
                return {'ok': True}
        return {'ok': False, 'error': 'Foydalanuvchi topilmadi'}

    @staticmethod
    def kick_user(user_id_or_query):
        data = load_db()
        q = str(user_id_or_query).strip().lower().replace('@', '')
        target_id = None
        for u in data['users'].values():
            if str(u.get('id')).lower() == q or u.get('username', '').lower() == q or u.get('email', '').lower() == q:
                if u.get('username') == 'BM_visual' or u.get('id') == 'admin_bm':
                    return {'ok': False, 'error': 'Bosh Super Adminni o\'chirib bo\'lmaydi!'}
                target_id = u['id']
                break
        if target_id and target_id in data['users']:
            user_info = data['users'][target_id]
            del data['users'][target_id]
            # Wipe all active sessions for this kicked user immediately
            data['sessions'] = {k: v for k, v in data['sessions'].items() if v.get('userId') != target_id}
            # Remove any pending receipts
            data['receipts'] = {k: v for k, v in data['receipts'].items() if v.get('userId') != target_id}
            save_db(data)
            return {'ok': True, 'message': f"Foydalanuvchi @{user_info.get('username')} platformadan butunlay chiqarib yuborildi."}
        return {'ok': False, 'error': 'Foydalanuvchi topilmadi'}

    @staticmethod
    def create_admin(email, username, password, full_name=''):
        data = load_db()
        email = email.strip().lower()
        username = username.strip().replace('@', '')
        
        for u in data['users'].values():
            if u.get('email', '').lower() == email:
                return {'ok': False, 'error': 'Bu Gmail bilan foydalanuvchi allaqachon mavjud!'}
            if u.get('username', '').lower() == username.lower():
                return {'ok': False, 'error': 'Bu Username allaqachon band qilingan!'}

        user_id = 'adm_' + uuid.uuid4().hex[:8]
        pass_hash = hash_password(password)
        now_ms = int(time.time() * 1000)

        new_admin = {
            'id': user_id,
            'email': email,
            'username': username,
            'fullName': full_name or username,
            'passwordHash': pass_hash,
            'role': 'admin',
            'joinedAt': now_ms,
            'subscriptionExpiresAt': 9999999999999,
            'subscriptionHistory': [],
            'receiptStatus': 'approved',
            'words': []
        }

        data['users'][user_id] = new_admin
        save_db(data)
        return {'ok': True, 'user': new_admin, 'message': 'Yangi Admin muvaffaqiyatli yaratildi!'}

    @staticmethod
    def promote_to_admin(user_id_or_query):
        data = load_db()
        q = str(user_id_or_query).strip().lower().replace('@', '')
        target = None
        for u in data['users'].values():
            if str(u.get('id')).lower() == q or u.get('username', '').lower() == q or u.get('email', '').lower() == q:
                target = u
                break
        if not target:
            return {'ok': False, 'error': 'Foydalanuvchi topilmadi'}
        
        target['role'] = 'admin'
        target['subscriptionExpiresAt'] = 9999999999999
        target['receiptStatus'] = 'approved'
        save_db(data)
        return {'ok': True, 'message': f"@{target.get('username')} muvaffaqiyatli Admin etib tayinlandi! 👑"}

    @staticmethod
    def demote_from_admin(user_id_or_query):
        data = load_db()
        q = str(user_id_or_query).strip().lower().replace('@', '')
        target = None
        for u in data['users'].values():
            if str(u.get('id')).lower() == q or u.get('username', '').lower() == q or u.get('email', '').lower() == q:
                target = u
                break
        if not target:
            return {'ok': False, 'error': 'Foydalanuvchi topilmadi'}
        
        if target.get('username') == 'BM_visual' or target.get('id') == 'admin_bm':
            return {'ok': False, 'error': 'Bosh Super Admin @BM_visual ni adminlikdan olib bo\'lmaydi!'}

        target['role'] = 'student'
        target['subscriptionExpiresAt'] = 0
        save_db(data)
        # remove current admin sessions so they must re-login as student
        data['sessions'] = {k: v for k, v in data['sessions'].items() if v.get('userId') != target['id']}
        save_db(data)
        return {'ok': True, 'message': f"@{target.get('username')} adminlik huquqi olib tashlandi."}

    @staticmethod
    def get_admins():
        data = load_db()
        admins = [u for u in data['users'].values() if u.get('role') == 'admin']
        return [{
            'id': a['id'],
            'email': a.get('email', ''),
            'username': a.get('username', ''),
            'fullName': a.get('fullName', ''),
            'role': 'admin',
            'joinedAt': a.get('joinedAt', 0),
            'isSuperAdmin': (a.get('username') == 'BM_visual' or a.get('id') == 'admin_bm')
        } for a in admins]

    @staticmethod
    def get_all_users():
        data = load_db()
        now_ms = int(time.time() * 1000)
        res = []
        for u in data['users'].values():
            exp = u.get('subscriptionExpiresAt', 0)
            is_admin = u.get('role') == 'admin'
            is_act = is_admin or (exp > now_ms)
            days_l = 9999 if is_admin else (int((exp - now_ms) / (1000 * 60 * 60 * 24)) + 1 if is_act else 0)
            res.append({
                'id': u['id'],
                'email': u.get('email', ''),
                'username': u.get('username', ''),
                'fullName': u.get('fullName', ''),
                'role': u.get('role', 'student'),
                'joinedAt': u.get('joinedAt', 0),
                'subscriptionExpiresAt': exp,
                'isActive': is_act,
                'daysLeft': days_l,
                'receiptStatus': u.get('receiptStatus', 'none'),
                'wordsCount': len(u.get('words', []))
            })
        res.sort(key=lambda x: x['joinedAt'], reverse=True)
        return res

    @staticmethod
    def get_stats():
        data = load_db()
        now_ms = int(time.time() * 1000)
        users = list(data['users'].values())
        students = [u for u in users if u.get('role') != 'admin']
        active_count = sum(1 for u in students if u.get('subscriptionExpiresAt', 0) > now_ms)
        expired_count = sum(1 for u in students if u.get('subscriptionExpiresAt', 0) <= now_ms)
        pending_receipts = sum(1 for r in data['receipts'].values() if r.get('status') == 'pending')
        stats = data.get('stats', {})

        return {
            'totalUsers': len(students),
            'activeCount': active_count,
            'expiredCount': expired_count,
            'pendingReceipts': pending_receipts,
            'totalRevenue': stats.get('totalRevenue', active_count * 50000),
            'approvedPayments': stats.get('approvedPayments', 0)
        }

    @staticmethod
    def save_words(user_id, words):
        data = load_db()
        if user_id in data['users']:
            data['users'][user_id]['words'] = words
            data['users'][user_id]['lastActive'] = int(time.time() * 1000)
            save_db(data)
            return True
        return False

    @staticmethod
    def get_words(user_id):
        data = load_db()
        user = data['users'].get(user_id)
        return user.get('words', []) if user else []
