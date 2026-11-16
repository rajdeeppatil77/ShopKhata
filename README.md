# ShopKhata – Smart Shop Credit Tracker

## Project Overview

**ShopKhata** is a lightweight Flask + SQLite web application designed for small grocery and general store owners to digitize their traditional *Khata* (credit ledger). It allows shop owners to track customer credit (udhar), record payments, manage balances, and send WhatsApp payment reminders — all from a simple browser-based interface with no internet dependency.

---

## Problem Statement

Small shop owners traditionally maintain handwritten credit ledgers (*Khatas*). This creates four recurring problems that ShopKhata directly solves:

1. **Losing track of customer dues** — Handwritten ledgers get lost, damaged, or become unreadable. ShopKhata persists all data in a local database with a full audit trail.
2. **Payment disputes (no receipts)** — Verbal credit agreements often lead to disputes. ShopKhata records every transaction with a unique ID and timestamp.
3. **Difficulty collecting payments** — Owners have no easy way to remind customers. ShopKhata generates pre-filled WhatsApp messages with one click.
4. **No monthly financial overview** — Owners cannot easily see how much is owed overall. ShopKhata provides a live dashboard and monthly/customer-level reports.

---

## Features

| Category | Feature |
|---|---|
| **Authentication** | Secure login/logout with hashed passwords and CSRF protection |
| **Dashboard** | Total outstanding balance, top debtors, recent activity summary, Chart.js visualizations |
| **Customer Management** | Add, edit, view customers; prevent deletion when balance is outstanding |
| **Credit Management** | Record credit transactions with item description, amount, and date |
| **Payment Management** | Record payments against outstanding balance; payments cannot exceed balance |
| **Ledger** | Full per-customer transaction history (credits + payments, chronological) |
| **Reports** | Monthly summary reports with totals and per-customer breakdown |
| **WhatsApp Reminders** | One-click pre-filled WhatsApp chat link for payment follow-ups |
| **Unique Transaction IDs** | Server-generated audit IDs for every credit and payment entry |

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5.3, Chart.js |
| **Backend** | Python 3.x, Flask 3.0 |
| **Database** | SQLite (via Python `sqlite3` standard library) |
| **Security** | Werkzeug password hashing, Flask-WTF CSRF protection, session-based authentication |

---

## Database Structure

The application uses **4 tables**:

```
users
 └── id (PK), username, password_hash, shop_name, created_at

customers
 └── id (PK), user_id (FK → users), name, phone, address, created_at

credit_transactions
 └── id (PK), transaction_id (unique), customer_id (FK → customers),
     user_id (FK → users), amount, description, date, created_at

payment_transactions
 └── id (PK), transaction_id (unique), customer_id (FK → customers),
     user_id (FK → users), amount, note, date, created_at
```

**Relationships:**
- One **user** owns many **customers** (1:N)
- One **customer** has many **credit_transactions** (1:N)
- One **customer** has many **payment_transactions** (1:N)
- Outstanding balance = `SUM(credit_transactions.amount) − SUM(payment_transactions.amount)` computed at query time

---

## Installation Instructions

### Prerequisites
- Python 3.8 or higher
- `pip` (comes with Python)
- Git

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/your-username/shop_credit_tracker.git
cd shop_credit_tracker
```

**2. Create and activate a virtual environment**

*macOS / Linux:*
```bash
python -m venv venv
source venv/bin/activate
```

*Windows:*
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Seed the database with demo data**
```bash
python seed.py
```
This creates the SQLite database (`shopkhata.db`) and populates it with a demo shop owner account and sample customers.

**5. Run the application**
```bash
python app.py
```

---

## How to Run

- **Development server:** `python app.py` → open [http://localhost:5000](http://localhost:5000) in your browser
- The app runs in Flask's built-in development server. For production deployment, use Gunicorn + Nginx.

---

## Demo Credentials

| Field | Value |
|-------|-------|
| Username | `demo` |
| Password | `demo123` |
| Shop Name | Ram General Store |

> Log in with the above credentials to explore the app with pre-loaded sample customers and transactions.

---

## Assumptions & Product Decisions

- **Balance is calculated from transactions** (not stored as a column) to prevent data inconsistency between the stored value and the actual transaction sum.
- **Customers cannot be deleted** if they have an outstanding balance — this protects data integrity and prevents accidental loss of debt records.
- **Payments cannot exceed outstanding balance** — enforced server-side to prevent negative balances.
- **Single-user per shop** — v1 targets individual shop owners; multi-staff role management is deferred to v2.
- **WhatsApp integration via click-to-chat** (`wa.me/`) — no API key or subscription required; works with any WhatsApp-enabled phone number.
- **Unique transaction IDs** are generated server-side (UUID-based) for every entry, enabling an audit trail without relying on auto-increment IDs alone.

---

## Features Excluded & Reasons

| Feature | Reason Excluded |
|---|---|
| SMS / Email notifications | Requires paid third-party API keys; out of scope for a free, offline-first tool |
| Multi-currency support | Target users are single-country small shop owners; adds unnecessary complexity |
| Inventory management | Out of scope; would double the complexity and shift the product's focus |
| Barcode scanning | Requires hardware integration not available in a pure web app |
| Multi-staff / role-based access | Planned for v2; v1 focuses on the solo shop owner use case |

---

## Future Improvements

- 📥 **Bulk import customers** via CSV upload
- 🔔 **Push notifications** for overdue payment reminders
- 📦 **Inventory integration** to auto-create credit entries from stock
- 🌐 **Multi-language support** (Hindi, Tamil, Telugu, and other regional languages)
- 📱 **PWA / offline support** so the app works without an internet connection
- 📧 **Monthly email statements** sent automatically to the shop owner

---

## Approximate Development Hours

| Phase | Hours |
|---|---|
| Project setup & architecture | 2 |
| Database & models | 3 |
| Authentication | 2 |
| Customer management | 3 |
| Credit & payment management | 4 |
| Dashboard | 3 |
| Reports | 2 |
| WhatsApp reminders | 1 |
| CSS / UI polish | 4 |
| Testing & debugging | 3 |
| Documentation | 2 |
| **Total** | **29** |

---

*Built with ❤️ for small shop owners everywhere.*
