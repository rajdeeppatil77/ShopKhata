"""
models.py — All database query functions for ShopKhata.
No ORM; uses raw sqlite3 via get_db() from shopkhata.__init__.
"""
import random
import string
from datetime import datetime

from shopkhata import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rand4():
    """Return 4 random digits as a string."""
    return ''.join(random.choices(string.digits, k=4))


# ---------------------------------------------------------------------------
# USER functions
# ---------------------------------------------------------------------------

def get_user_by_username(username):
    """Return the user row matching *username*, or None."""
    db = get_db()
    return db.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()


def get_user_by_id(user_id):
    """Return the user row matching *user_id*, or None."""
    db = get_db()
    return db.execute(
        'SELECT * FROM users WHERE id = ?', (user_id,)
    ).fetchone()


def create_user(username, password_hash, shop_name):
    """Insert a new user and return its id."""
    db = get_db()
    cursor = db.execute(
        'INSERT INTO users (username, password_hash, shop_name) VALUES (?, ?, ?)',
        (username, password_hash, shop_name)
    )
    db.commit()
    return cursor.lastrowid


# ---------------------------------------------------------------------------
# CUSTOMER functions
# ---------------------------------------------------------------------------

def get_customer_balance(customer_id, user_id=None):
    """Return the net balance (credits − payments) for a customer as a float."""
    db = get_db()
    if user_id is not None:
        row = db.execute(
            """
            SELECT
                COALESCE((SELECT SUM(amount) FROM credit_transactions WHERE customer_id = ? AND user_id = ?), 0) -
                COALESCE((SELECT SUM(amount) FROM payment_transactions WHERE customer_id = ? AND user_id = ?), 0)
                AS balance
            """,
            (customer_id, user_id, customer_id, user_id)
        ).fetchone()
    else:
        row = db.execute(
            """
            SELECT
                COALESCE((SELECT SUM(amount) FROM credit_transactions WHERE customer_id = ?), 0) -
                COALESCE((SELECT SUM(amount) FROM payment_transactions WHERE customer_id = ?), 0)
                AS balance
            """,
            (customer_id, customer_id)
        ).fetchone()
    return float(row['balance']) if row else 0.0


def get_customers_with_balance(user_id):
    """Return all customers for *user_id* sorted by outstanding balance (desc)."""
    db = get_db()
    return db.execute(
        """
        SELECT
            c.*,
            COALESCE(cr.total_credit, 0) AS total_credit,
            COALESCE(py.total_paid, 0) AS total_paid,
            COALESCE(cr.total_credit, 0) - COALESCE(py.total_paid, 0) AS balance
        FROM customers c
        LEFT JOIN (
            SELECT customer_id, SUM(amount) AS total_credit
            FROM credit_transactions
            WHERE user_id = ?
            GROUP BY customer_id
        ) cr ON cr.customer_id = c.id
        LEFT JOIN (
            SELECT customer_id, SUM(amount) AS total_paid
            FROM payment_transactions
            WHERE user_id = ?
            GROUP BY customer_id
        ) py ON py.customer_id = c.id
        WHERE c.user_id = ?
        ORDER BY balance DESC, c.full_name ASC
        """,
        (user_id, user_id, user_id)
    ).fetchall()


def get_customers(user_id, search=None):
    """
    Return a list of customer rows (with computed *balance*) for *user_id*.
    Optionally filter by *search* (matches full_name or phone).
    """
    db = get_db()
    if search:
        search_param = f"%{search.strip()}%"
        return db.execute(
            """
            SELECT
                c.*,
                COALESCE(cr.total_credit, 0) AS total_credit,
                COALESCE(py.total_paid, 0) AS total_paid,
                COALESCE(cr.total_credit, 0) - COALESCE(py.total_paid, 0) AS balance
            FROM customers c
            LEFT JOIN (
                SELECT customer_id, SUM(amount) AS total_credit
                FROM credit_transactions
                WHERE user_id = ?
                GROUP BY customer_id
            ) cr ON cr.customer_id = c.id
            LEFT JOIN (
                SELECT customer_id, SUM(amount) AS total_paid
                FROM payment_transactions
                WHERE user_id = ?
                GROUP BY customer_id
            ) py ON py.customer_id = c.id
            WHERE c.user_id = ? AND (c.full_name LIKE ? OR c.phone LIKE ?)
            ORDER BY balance DESC, c.full_name ASC
            """,
            (user_id, user_id, user_id, search_param, search_param)
        ).fetchall()
    return get_customers_with_balance(user_id)


search_customers = get_customers


def get_customer(customer_id, user_id):
    """Return single customer row with total_credit, total_paid, balance, or None."""
    db = get_db()
    return db.execute(
        """
        SELECT
            c.*,
            COALESCE(cr.total_credit, 0) AS total_credit,
            COALESCE(py.total_paid, 0) AS total_paid,
            COALESCE(cr.total_credit, 0) - COALESCE(py.total_paid, 0) AS balance
        FROM customers c
        LEFT JOIN (
            SELECT customer_id, SUM(amount) AS total_credit
            FROM credit_transactions
            WHERE user_id = ?
            GROUP BY customer_id
        ) cr ON cr.customer_id = c.id
        LEFT JOIN (
            SELECT customer_id, SUM(amount) AS total_paid
            FROM payment_transactions
            WHERE user_id = ?
            GROUP BY customer_id
        ) py ON py.customer_id = c.id
        WHERE c.id = ? AND c.user_id = ?
        """,
        (user_id, user_id, customer_id, user_id)
    ).fetchone()


def customer_exists(user_id, full_name, phone=None, exclude_id=None):
    """Check if customer with same name and phone already exists for this shop owner."""
    db = get_db()
    clean_name = full_name.strip()
    clean_phone = phone.strip() if phone else None

    if clean_phone:
        if exclude_id:
            row = db.execute(
                "SELECT id FROM customers WHERE user_id = ? AND LOWER(full_name) = LOWER(?) AND phone = ? AND id != ?",
                (user_id, clean_name, clean_phone, exclude_id)
            ).fetchone()
        else:
            row = db.execute(
                "SELECT id FROM customers WHERE user_id = ? AND LOWER(full_name) = LOWER(?) AND phone = ?",
                (user_id, clean_name, clean_phone)
            ).fetchone()
    else:
        if exclude_id:
            row = db.execute(
                "SELECT id FROM customers WHERE user_id = ? AND LOWER(full_name) = LOWER(?) AND (phone IS NULL OR phone = '') AND id != ?",
                (user_id, clean_name, exclude_id)
            ).fetchone()
        else:
            row = db.execute(
                "SELECT id FROM customers WHERE user_id = ? AND LOWER(full_name) = LOWER(?) AND (phone IS NULL OR phone = '')",
                (user_id, clean_name)
            ).fetchone()
    return row is not None


def create_customer(user_id, full_name, phone=None, address=None):
    """Insert a new customer and return customer_id."""
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO customers (user_id, full_name, phone, address)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, full_name, phone, address)
    )
    db.commit()
    return cursor.lastrowid


def update_customer(customer_id, user_id, full_name, phone=None, address=None):
    """Update customer details."""
    db = get_db()
    cursor = db.execute(
        """
        UPDATE customers
        SET full_name = ?, phone = ?, address = ?
        WHERE id = ? AND user_id = ?
        """,
        (full_name, phone, address, customer_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def delete_customer(customer_id, user_id):
    """
    Delete customer only if current balance is 0.
    Returns True if deleted, False if balance != 0 or not found.
    """
    customer = get_customer(customer_id, user_id)
    if customer is None:
        return False
    balance = get_customer_balance(customer_id, user_id)
    if abs(balance) > 0.001:
        return False
    db = get_db()
    db.execute(
        "DELETE FROM credit_transactions WHERE customer_id = ? AND user_id = ?",
        (customer_id, user_id)
    )
    db.execute(
        "DELETE FROM payment_transactions WHERE customer_id = ? AND user_id = ?",
        (customer_id, user_id)
    )
    cursor = db.execute(
        "DELETE FROM customers WHERE id = ? AND user_id = ?",
        (customer_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# CREDIT TRANSACTION functions
# ---------------------------------------------------------------------------

def get_credits(customer_id, user_id):
    """Return all credit transactions for a customer."""
    db = get_db()
    return db.execute(
        """
        SELECT * FROM credit_transactions
        WHERE customer_id = ? AND user_id = ?
        ORDER BY txn_date DESC, created_at DESC
        """,
        (customer_id, user_id)
    ).fetchall()


def add_credit(customer_id, user_id, description, amount, txn_date, notes=None):
    """Insert a credit transaction and return the generated txn_id."""
    customer = get_customer(customer_id, user_id)
    if customer is None:
        raise ValueError(f"Customer #{customer_id} not found for this shop owner.")
    if amount <= 0:
        raise ValueError("Credit amount must be greater than zero.")

    txn_id = 'CR' + datetime.now().strftime('%Y%m%d%H%M%S') + _rand4()
    db = get_db()
    db.execute(
        """
        INSERT INTO credit_transactions
            (customer_id, user_id, txn_id, description, amount, txn_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (customer_id, user_id, txn_id, description, amount, txn_date, notes)
    )
    db.commit()
    return txn_id


add_credit_transaction = add_credit


def get_recent_transactions(user_id, limit=10):
    """Return the most recent combined credit and payment transactions."""
    db = get_db()
    return db.execute(
        """
        SELECT * FROM (
            SELECT
                ct.txn_id, 'credit' AS type, ct.amount, ct.txn_date,
                ct.description, c.full_name AS customer_name,
                ct.customer_id, ct.created_at
            FROM credit_transactions ct
            JOIN customers c ON c.id = ct.customer_id
            WHERE ct.user_id = ?

            UNION ALL

            SELECT
                pt.txn_id, 'payment' AS type, pt.amount, pt.txn_date,
                'Payment Received' AS description, c.full_name AS customer_name,
                pt.customer_id, pt.created_at
            FROM payment_transactions pt
            JOIN customers c ON c.id = pt.customer_id
            WHERE pt.user_id = ?
        )
        ORDER BY txn_date DESC, created_at DESC
        LIMIT ?
        """,
        (user_id, user_id, limit)
    ).fetchall()


# ---------------------------------------------------------------------------
# PAYMENT TRANSACTION functions
# ---------------------------------------------------------------------------

def get_payments(customer_id, user_id):
    """Return all payment transactions for a customer."""
    db = get_db()
    return db.execute(
        """
        SELECT * FROM payment_transactions
        WHERE customer_id = ? AND user_id = ?
        ORDER BY txn_date DESC, created_at DESC
        """,
        (customer_id, user_id)
    ).fetchall()


def add_payment(customer_id, user_id, amount, txn_date, notes=None):
    """Insert payment transaction. Raises ValueError if amount > balance, balance is zero, or customer not found."""
    customer = get_customer(customer_id, user_id)
    if customer is None:
        raise ValueError(f"Customer #{customer_id} not found for this shop owner.")
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    balance = get_customer_balance(customer_id, user_id)
    if balance <= 0.001:
        raise ValueError(f"Customer '{customer['full_name']}' currently has no outstanding balance (₹0.00).")
    if amount > round(balance, 2) + 0.01:
        raise ValueError(
            f'Payment amount ₹{amount:.2f} exceeds outstanding balance ₹{balance:.2f}'
        )

    txn_id = 'PAY' + datetime.now().strftime('%Y%m%d%H%M%S') + _rand4()
    db = get_db()
    db.execute(
        """
        INSERT INTO payment_transactions
            (customer_id, user_id, txn_id, amount, txn_date, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (customer_id, user_id, txn_id, amount, txn_date, notes)
    )
    db.commit()
    return txn_id


add_payment_transaction = add_payment


# ---------------------------------------------------------------------------
# LEDGER function
# ---------------------------------------------------------------------------

def get_ledger(customer_id, user_id):
    """Return customer ledger entries with running balance and transaction IDs."""
    customer = get_customer(customer_id, user_id)
    if customer is None:
        return None

    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM (
            SELECT txn_id, txn_date AS date, 'credit' AS type, description, amount, notes, created_at
            FROM credit_transactions
            WHERE customer_id = ? AND user_id = ?

            UNION ALL

            SELECT txn_id, txn_date AS date, 'payment' AS type, 'Payment Received' AS description, amount, notes, created_at
            FROM payment_transactions
            WHERE customer_id = ? AND user_id = ?
        )
        ORDER BY date ASC, created_at ASC
        """,
        (customer_id, user_id, customer_id, user_id)
    ).fetchall()

    entries = []
    running = 0.0
    for row in rows:
        if row['type'] == 'credit':
            running += row['amount']
            entry = {
                'txn_id': row['txn_id'],
                'date': row['date'],
                'type': 'credit',
                'description': row['description'],
                'notes': row['notes'],
                'debit': row['amount'],
                'credit': 0,
                'running_balance': running,
            }
        else:
            running -= row['amount']
            entry = {
                'txn_id': row['txn_id'],
                'date': row['date'],
                'type': 'payment',
                'description': row['description'],
                'notes': row['notes'],
                'debit': 0,
                'credit': row['amount'],
                'running_balance': running,
            }
        entries.append(entry)

    return {
        'customer': customer,
        'entries': entries,
        'balance': float(customer['balance']),
    }


# ---------------------------------------------------------------------------
# DASHBOARD / STATS function
# ---------------------------------------------------------------------------

def get_dashboard_stats(user_id):
    """Return all dashboard statistics and metrics."""
    db = get_db()

    total_customers = db.execute(
        'SELECT COUNT(*) AS n FROM customers WHERE user_id = ?', (user_id,)
    ).fetchone()['n']

    totals = db.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN t = 'c' THEN amount ELSE 0 END), 0) AS total_credit,
            COALESCE(SUM(CASE WHEN t = 'p' THEN amount ELSE 0 END), 0) AS total_paid
        FROM (
            SELECT amount, 'c' AS t FROM credit_transactions WHERE user_id = ?
            UNION ALL
            SELECT amount, 'p' AS t FROM payment_transactions WHERE user_id = ?
        )
        """,
        (user_id, user_id)
    ).fetchone()

    total_credit_given = round(float(totals['total_credit']), 2)
    total_payments_received = round(float(totals['total_paid']), 2)

    customers_with_bal = get_customers_with_balance(user_id)
    total_outstanding = round(sum(float(c['balance']) for c in customers_with_bal if c['balance'] > 0), 2)

    recent_transactions = get_recent_transactions(user_id, limit=8)
    top_pending_customers = [c for c in customers_with_bal if c['balance'] > 0][:5]

    return {
        'total_customers': total_customers,
        'total_outstanding': total_outstanding,
        'total_credit_given': total_credit_given,
        'total_payments_received': total_payments_received,
        'recent_transactions': recent_transactions,
        'top_pending_customers': top_pending_customers,
    }


# ---------------------------------------------------------------------------
# REPORTS function
# ---------------------------------------------------------------------------

def get_report_data(user_id):
    """Return report data for UI and CSV export."""
    db = get_db()
    customers = get_customers_with_balance(user_id)
    customer_balances = [
        {
            'customer_id': c['id'],
            'full_name': c['full_name'],
            'customer_name': c['full_name'],
            'phone': c['phone'] or '',
            'address': c['address'] or '',
            'total_credit': float(c['total_credit']),
            'total_paid': float(c['total_paid']),
            'balance': float(c['balance']),
            'outstanding': float(c['balance']),
        }
        for c in customers
    ]

    monthly_rows = db.execute(
        """
        SELECT
            strftime('%Y-%m', date) AS month,
            SUM(CASE WHEN type = 'c' THEN amount ELSE 0 END) AS total_credit,
            SUM(CASE WHEN type = 'p' THEN amount ELSE 0 END) AS total_paid
        FROM (
            SELECT txn_date AS date, amount, 'c' AS type
            FROM credit_transactions
            WHERE user_id = ?
            UNION ALL
            SELECT txn_date AS date, amount, 'p' AS type
            FROM payment_transactions
            WHERE user_id = ?
        )
        GROUP BY month
        ORDER BY month DESC
        """,
        (user_id, user_id)
    ).fetchall()

    monthly_summary = [
        {
            'month': r['month'],
            'total_credit': float(r['total_credit']),
            'total_paid': float(r['total_paid']),
            'net': float(r['total_credit']) - float(r['total_paid']),
        }
        for r in monthly_rows
    ]

    total_credit = round(sum(c['total_credit'] for c in customer_balances), 2)
    total_paid = round(sum(c['total_paid'] for c in customer_balances), 2)
    total_outstanding = round(sum(c['balance'] for c in customer_balances if c['balance'] > 0), 2)

    return {
        'customer_balances': customer_balances,
        'monthly_summary': monthly_summary,
        'totals': {
            'total_credit': total_credit,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
        },
    }
