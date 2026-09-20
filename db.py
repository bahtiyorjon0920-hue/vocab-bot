import os
import json
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_FILE = os.path.join(DATA_DIR, 'database.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

def load_db():
    if not os.path.exists(DB_FILE):
        initial = {
            'users': {},
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
            return json.load(f)
    except Exception as e:
        print('Database read error:', e)
        return {'users': {}, 'stats': {}}

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print('Database save error:', e)

class Database:
    @staticmethod
    def get_user(telegram_id):
        data = load_db()
        return data['users'].get(str(telegram_id))

    @staticmethod
    def register_or_update_user(telegram_id, info=None):
        info = info or {}
        data = load_db()
        user_id = str(telegram_id)
        now_ms = int(time.time() * 1000)

        if user_id not in data['users']:
            username = info.get('username', '')
            if username and not username.startswith('@'):
                username = f'@{username}'

            data['users'][user_id] = {
                'id': user_id,
                'username': username,
                'firstName': info.get('firstName', ''),
                'lastName': info.get('lastName', ''),
                'joinedAt': now_ms,
                'subscriptionExpiresAt': 0,
                'subscriptionHistory': [],
                'words': []
            }
        else:
            u = data['users'][user_id]
            if 'username' in info and info['username']:
                un = info['username']
                u['username'] = un if un.startswith('@') else f'@{un}'
            if 'firstName' in info and info['firstName']:
                u['firstName'] = info['firstName']
            if 'lastName' in info and info['lastName']:
                u['lastName'] = info['lastName']

        save_db(data)
        return data['users'][user_id]

    @staticmethod
    def add_subscription(telegram_id, days=30, amount=50000, granted_by='admin'):
        data = load_db()
        user_id = str(telegram_id)
        if user_id not in data['users']:
            Database.register_or_update_user(user_id)
            data = load_db()

        user = data['users'][user_id]
        now_ms = int(time.time() * 1000)
        current_exp = user.get('subscriptionExpiresAt', 0)

        base_time = current_exp if current_exp > now_ms else now_ms
        added_ms = days * 24 * 60 * 60 * 1000
        user['subscriptionExpiresAt'] = base_time + added_ms

        if 'subscriptionHistory' not in user:
            user['subscriptionHistory'] = []
        user['subscriptionHistory'].append({
            'date': now_ms,
            'days': days,
            'amount': amount,
            'grantedBy': granted_by,
            'expiresAt': user['subscriptionExpiresAt']
        })

        if 'stats' not in data:
            data['stats'] = {'totalRevenue': 0, 'approvedPayments': 0}
        data['stats']['totalRevenue'] = data['stats'].get('totalRevenue', 0) + amount
        data['stats']['approvedPayments'] = data['stats'].get('approvedPayments', 0) + 1

        save_db(data)
        days_left = max(0, int((user['subscriptionExpiresAt'] - now_ms) / (1000 * 60 * 60 * 24)))
        return {
            'user': user,
            'expiresAt': user['subscriptionExpiresAt'],
            'daysLeft': days_left
        }

    @staticmethod
    def remove_subscription(telegram_id):
        data = load_db()
        user_id = str(telegram_id)
        if user_id in data['users']:
            data['users'][user_id]['subscriptionExpiresAt'] = 0
            save_db(data)
            return True
        return False

    @staticmethod
    def is_subscribed(telegram_id):
        admin_id = os.getenv('ADMIN_ID', '').strip()
        if admin_id and str(telegram_id).strip() == admin_id:
            return True
        user = Database.get_user(telegram_id)
        if not user:
            return False
        now_ms = int(time.time() * 1000)
        return user.get('subscriptionExpiresAt', 0) > now_ms

    @staticmethod
    def get_remaining_days(telegram_id):
        admin_id = os.getenv('ADMIN_ID', '').strip()
        if admin_id and str(telegram_id).strip() == admin_id:
            return 9999
        user = Database.get_user(telegram_id)
        if not user:
            return 0
        now_ms = int(time.time() * 1000)
        exp = user.get('subscriptionExpiresAt', 0)
        if exp <= now_ms:
            return 0
        return max(0, int((exp - now_ms) / (1000 * 60 * 60 * 24))) + 1

    @staticmethod
    def save_words(telegram_id, words):
        data = load_db()
        user_id = str(telegram_id)
        if user_id not in data['users']:
            Database.register_or_update_user(user_id)
            data = load_db()

        data['users'][user_id]['words'] = words
        data['users'][user_id]['lastActive'] = int(time.time() * 1000)
        save_db(data)
        return True

    @staticmethod
    def get_words(telegram_id):
        user = Database.get_user(telegram_id)
        return user.get('words', []) if user else []

    @staticmethod
    def get_all_users():
        data = load_db()
        now_ms = int(time.time() * 1000)
        res = []
        for u in data['users'].values():
            exp = u.get('subscriptionExpiresAt', 0)
            is_act = exp > now_ms
            days_l = int((exp - now_ms) / (1000 * 60 * 60 * 24)) + 1 if is_act else 0
            res.append({
                **u,
                'isActive': is_act,
                'daysLeft': days_l
            })
        return res

    @staticmethod
    def find_user(query):
        data = load_db()
        q = str(query).strip().lower().replace('@', '')
        for u in data['users'].values():
            if str(u.get('id')) == q:
                return u
            un = (u.get('username') or '').lower().replace('@', '')
            if un == q:
                return u
        return None

    @staticmethod
    def get_stats():
        data = load_db()
        now_ms = int(time.time() * 1000)
        users = list(data['users'].values())
        active_count = sum(1 for u in users if u.get('subscriptionExpiresAt', 0) > now_ms)
        expired_count = sum(1 for u in users if 0 < u.get('subscriptionExpiresAt', 0) <= now_ms)
        stats = data.get('stats', {})

        return {
            'totalUsers': len(users),
            'activeCount': active_count,
            'expiredCount': expired_count,
            'totalRevenue': stats.get('totalRevenue', active_count * 50000),
            'approvedPayments': stats.get('approvedPayments', 0)
        }
