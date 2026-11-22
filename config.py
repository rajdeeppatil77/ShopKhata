import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')


def _load_secret_key():
    """Use SECRET_KEY env var, else a key persisted in instance/secret_key.

    A random key generated on every start would log Ravi out every time the
    server restarts (and on every auto-reload in debug mode).
    """
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    path = os.path.join(INSTANCE_DIR, 'secret_key')
    if os.path.exists(path):
        with open(path) as f:
            key = f.read().strip()
        if key:
            return key
    key = secrets.token_hex(32)
    with open(path, 'w') as f:
        f.write(key)
    return key


class Config:
    SECRET_KEY = _load_secret_key()
    # DATABASE_PATH lets tests use a throw-away database.
    DATABASE = os.environ.get('DATABASE_PATH') or os.path.join(INSTANCE_DIR, 'shopkhata.db')
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30  # 30 days
