import os, secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'shopkhata.db')
    WTF_CSRF_ENABLED = True
