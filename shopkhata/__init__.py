import sqlite3
import os
from flask import Flask, g, current_app, jsonify, session
from flask_wtf.csrf import CSRFProtect
from shopkhata.utils import format_currency, format_date

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    csrf.init_app(app)

    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

    # Register template filters
    @app.template_filter('currency')
    def currency_filter(val):
        return format_currency(val)

    @app.template_filter('date_format')
    def date_filter(val):
        return format_date(val)

    # Register blueprints
    from .auth import bp as auth_bp
    from .customers import bp as customers_bp
    from .transactions import bp as transactions_bp
    from .dashboard import bp as dashboard_bp
    from .reports import bp as reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)

    # API route for AJAX dynamic balance lookup
    @app.route('/api/balance/<int:customer_id>')
    def api_customer_balance(customer_id):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        from shopkhata import models
        customer = models.get_customer(customer_id, user_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        balance = models.get_customer_balance(customer_id, user_id)
        return jsonify({
            'customer_id': customer_id,
            'customer_name': customer['full_name'],
            'balance': balance,
            'formatted': format_currency(balance)
        })

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    return app


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    shop_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credit_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    txn_id TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    txn_date TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payment_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    txn_id TEXT UNIQUE NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    txn_date TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_customers_user ON customers(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_user_cust ON credit_transactions(user_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_user_cust ON payment_transactions(user_id, customer_id);
    """)
    db.commit()
