import json
import hashlib

USER_DB = 'users.json'

def load_users():
    with open(USER_DB, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB, 'w') as f:
        json.dump(users, f, indent=4)
        
#SHA-256 Hashing to secure passwords.
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    users = load_users()
    if any(user['username'] == username for user in users):
        return False
    users.append({'username': username, 'password': hash_password(password)})
    save_users(users)
    return True

def login_user(username, password):
    users = load_users()
    hashed_password = hash_password(password)
    for user in users:
        if user['username'] == username and user['password'] == hashed_password:
            return True
    return False
