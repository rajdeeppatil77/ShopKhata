"""
seed.py — Seed the ShopKhata database with demo data.

Usage:
    python seed.py

Creates the database if it doesn't exist, then inserts:
  - 1 demo user  (demo / demo123)
  - 15 fictional Hyderabad customers
  - 2-5 credit transactions per customer
  - 1-3 payments per customer
  - Transactions spread over the last 3 months
"""

import os
import sys
import random
import string
from datetime import datetime, timedelta

# Ensure project root is on sys.path so "from shopkhata import ..." works.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from werkzeug.security import generate_password_hash
from shopkhata import create_app, get_db, init_db


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"
DEMO_SHOP     = "Ravi Kirana Store"

CUSTOMERS = [
    ("Lakshmi Reddy",     "9848012345", "Flat 201, Srinivasa Apts, Ameerpet, Hyderabad"),
    ("Venkatesh Rao",     "9848023456", "H.No 4-5-67, Kukatpally, Hyderabad"),
    ("Anjali Devi",       "9701034567", "Plot 12, SR Nagar, Hyderabad"),
    ("Srinivas Goud",     "9701045678", "8-2-120, Banjara Hills Road 3, Hyderabad"),
    ("Padma Kumari",      "9912056789", "Door 5-9-14, Secunderabad"),
    ("Mohammed Irfan",    "9912067890", "11-4-55, Tolichowki, Hyderabad"),
    ("Sunitha Naidu",     "9989078901", "Flat 3B, Madhapur, Hyderabad"),
    ("Ramesh Babu",       "9989089012", "2-1-33, Nampally, Hyderabad"),
    ("Fatima Begum",      "9849090123", "16-7-9, Charminar Road, Hyderabad"),
    ("Krishna Murthy",    "9849101234", "Plot 44, Dilsukhnagar, Hyderabad"),
    ("Swapna Yadav",      "9700112345", "5-3-21, Mehdipatnam, Hyderabad"),
    ("Naresh Kumar",      "9700123456", "H.No 7-1-8, Begumpet, Hyderabad"),
    ("Bhavani Shankar",   "8099134567", "Flat 102, Gachibowli, Hyderabad"),
    ("Rukmini Bai",       "8099145678", "3-6-2, Himayatnagar, Hyderabad"),
    ("Anwar Hussain",     "8008156789", "9-8-77, Malakpet, Hyderabad"),
]

CREDIT_ITEMS = [
    ("Wheat flour (10 kg)",  450),
    ("Rice (5 kg)",          300),
    ("Sugar (2 kg)",         120),
    ("Refined oil (1 L)",    180),
    ("Dal (1 kg)",           130),
    ("Milk (1 L)",            60),
    ("Salt (1 kg)",           25),
    ("Tea (500 g)",          180),
    ("Biscuits (assorted)",   85),
    ("Soap (pack of 4)",     120),
    ("Detergent (1 kg)",     200),
    ("Spices (mixed)",       350),
    ("Butter (500 g)",       280),
    ("Paneer (500 g)",       260),
    ("Chips (family pack)",   95),
    ("Cold drink (2 L)",      90),
    ("Namkeen (500 g)",      110),
    ("Ghee (500 g)",         550),
    ("Maida (5 kg)",         200),
    ("Tomato ketchup",       130),
    ("Noodles (12 pack)",    180),
    ("Lentils (2 kg)",       240),
    ("Chana dal (1 kg)",     115),
    ("Cornflakes (500 g)",   220),
    ("Bread (2 loaves)",     100),
]


_counter = 0
def rand4():
    global _counter
    _counter += 1
    return f"{_counter:04d}" + ''.join(random.choices(string.digits, k=4))


def random_date_last_90_days():
    """Return a date string (YYYY-MM-DD) within the last 90 days."""
    offset = random.randint(0, 90)
    dt = datetime.now() - timedelta(days=offset)
    return dt.strftime('%Y-%m-%d')


def seed():
    random.seed(2026)  # same demo data on every run
    app = create_app()

    with app.app_context():
        db = get_db()

        # ------------------------------------------------------------------ #
        # 1. Demo user
        # ------------------------------------------------------------------ #
        existing = db.execute(
            'SELECT id FROM users WHERE username = ?', (DEMO_USERNAME,)
        ).fetchone()

        if existing:
            user_id = existing['id']
            print(f"[seed] Demo user already exists (id={user_id}), reusing.")
        else:
            pwd_hash = generate_password_hash(DEMO_PASSWORD)
            cur = db.execute(
                'INSERT INTO users (username, password_hash, shop_name) VALUES (?, ?, ?)',
                (DEMO_USERNAME, pwd_hash, DEMO_SHOP)
            )
            db.commit()
            user_id = cur.lastrowid
            print(f"[seed] Created demo user (id={user_id}).")

        # ------------------------------------------------------------------ #
        # 2. Customers
        # ------------------------------------------------------------------ #
        # Clear any existing seed data for this user so the script is idempotent
        existing_customers = db.execute(
            'SELECT id FROM customers WHERE user_id = ?', (user_id,)
        ).fetchall()
        existing_ids = [r['id'] for r in existing_customers]
        if existing_ids:
            placeholders = ','.join('?' * len(existing_ids))
            db.execute(f'DELETE FROM credit_transactions  WHERE customer_id IN ({placeholders})', existing_ids)
            db.execute(f'DELETE FROM payment_transactions WHERE customer_id IN ({placeholders})', existing_ids)
            db.execute(f'DELETE FROM customers WHERE user_id = ?', (user_id,))
            db.commit()
            print(f"[seed] Cleared {len(existing_ids)} existing customers.")

        total_credits  = 0
        total_payments = 0

        for full_name, phone, address in CUSTOMERS:
            # Insert customer
            cur = db.execute(
                'INSERT INTO customers (user_id, full_name, phone, address) VALUES (?, ?, ?, ?)',
                (user_id, full_name, phone, address)
            )
            db.commit()
            customer_id = cur.lastrowid

            # ---- Credit transactions (2–5) --------------------------------
            n_credits = random.randint(2, 5)
            credit_total = 0.0
            items_used = random.sample(CREDIT_ITEMS, n_credits)
            for item_name, base_price in items_used:
                # Vary the price ±20 %
                amount = round(base_price * random.uniform(0.8, 1.2), 2)
                txn_date = random_date_last_90_days()
                txn_id   = 'CR' + datetime.now().strftime('%Y%m%d%H%M%S') + rand4()
                db.execute(
                    """
                    INSERT INTO credit_transactions
                        (customer_id, user_id, txn_id, description, amount, txn_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (customer_id, user_id, txn_id, item_name, amount, txn_date, None)
                )
                db.commit()
                credit_total += amount
                total_credits += 1

            # ---- Payment transactions (1–3, partial or full) ---------------
            n_payments = random.randint(1, 3)
            paid_so_far = 0.0
            remaining   = credit_total

            for i in range(n_payments):
                if remaining <= 0:
                    break
                # Last payment may clear the balance; earlier ones are partial
                if i == n_payments - 1 and random.random() < 0.4:
                    pay_amount = round(remaining, 2)          # clear balance
                else:
                    pay_amount = round(remaining * random.uniform(0.2, 0.6), 2)
                    pay_amount = max(pay_amount, 50.0)        # min ₹50 payment
                    pay_amount = min(pay_amount, remaining)

                if pay_amount <= 0:
                    break

                txn_date = random_date_last_90_days()
                txn_id   = 'PAY' + datetime.now().strftime('%Y%m%d%H%M%S') + rand4()
                db.execute(
                    """
                    INSERT INTO payment_transactions
                        (customer_id, user_id, txn_id, amount, txn_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (customer_id, user_id, txn_id, pay_amount, txn_date, 'Cash payment')
                )
                db.commit()
                remaining   -= pay_amount
                paid_so_far += pay_amount
                total_payments += 1

        # ------------------------------------------------------------------ #
        # 3. Summary
        # ------------------------------------------------------------------ #
        print(
            f"\nDemo login: {DEMO_USERNAME} / {DEMO_PASSWORD}, "
            f"{len(CUSTOMERS)} customers, "
            f"{total_credits + total_payments} transactions seeded "
            f"({total_credits} credits, {total_payments} payments)"
        )


if __name__ == '__main__':
    seed()
