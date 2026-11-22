# ShopKhata – Shop Credit Tracker for Ravi

A small web app that replaces the paper *khata* notebook of a neighbourhood grocery shop.

## 1. The problem and the user

**User:** Ravi runs a small grocery shop in Hyderabad and gives goods on credit to about 80 regular customers. He uses a smartphone every day, reads simple English, is not comfortable with complicated apps, and is usually busy with a customer standing at the counter.

**His problems (from the brief):**
1. "I forget who owes me how much. Sometimes I lose the money completely."
2. "Customers argue: 'I paid you last week!' I have no proof."
3. "Asking people to pay is awkward. I don't remind them, so they delay."
4. "At the end of the month I don't know how much money is stuck with customers."

I tried to address all four, but kept each solution small.

| Ravi's problem | How ShopKhata solves it |
|---|---|
| Forgets who owes what | Customer list sorted by who owes most; search by name or phone; dashboard shows total outstanding and top debtors |
| "I paid last week!" | Every credit and payment is saved with a date and a unique entry ID. Each customer has a ledger with a running balance, so Ravi can show the exact history |
| Awkward to ask for money | One tap on a customer opens WhatsApp with a polite, pre-filled reminder that includes the amount |
| Month-end: how much is stuck? | Dashboard + Reports page: total credit given, total received, total outstanding, month-by-month summary, and a CSV download |

## 2. What I built

- Login / logout, with a separate private set of data for each shop (all queries are scoped to the logged-in user).
- Customers: add, edit, search, view ledger, delete (only when the balance is zero).
- **Quick Credit** and **Quick Payment** screens. Only *customer* and *amount* are needed; the date defaults to today and the item description is optional, so an entry takes a few seconds.
- Per-customer ledger with running balance and entry IDs.
- WhatsApp reminder link (opens a pre-filled message; nothing is sent automatically).
- Dashboard and monthly reports, CSV export.
- Mobile-first layout (Bootstrap 5), large buttons and inputs.
- Seed script with 15 Hyderabad customers and about 80 entries, plus a demo login.
- 18 automated tests (auth, CSRF, tenant isolation, money rules, input validation, XSS/SQL-injection checks, regressions).

### Deliberately left out (and why)

| Left out | Reason |
|---|---|
| SMS / automatic WhatsApp sending | Needs paid APIs; the brief says no outside integrations. A click-to-chat link needs no API key |
| Editing / deleting individual entries | A ledger that can be silently edited weakens the "proof" Ravi needs. A wrong entry should be fixed with a new correcting entry (see next steps) |
| Inventory, billing, GST | Different product; would hide the one thing Ravi needs |
| Staff accounts / roles | v1 is for one owner |
| Telugu / Hindi UI | Ravi reads simple English; language support is a next step |
| Hosting | Not required; the app runs locally |

## 3. Assumptions and product decisions

- All amounts are in rupees. Balance is **never stored**; it is always calculated as total credit − total payments, so it cannot drift out of sync.
- A payment cannot be larger than what the customer owes (prevents typing mistakes such as an extra zero). Advance payments are not supported in v1.
- Customers with any balance cannot be deleted; this protects debt records.
- Phone numbers are 10-digit Indian mobile numbers (optional). A customer without a phone simply has no WhatsApp button.
- Entry IDs are generated on the server (timestamp + random digits) and are unique in the database.
- The item description is optional (stored as "Goods on credit" if blank), because typing at the counter is the slowest part.
- Dates are plain `YYYY-MM-DD` in the shop's local time.
- Registration is open so the reviewer can create a second shop and verify that data is private.
- **Internet note:** Bootstrap, Bootstrap Icons, Chart.js and the Inter font are loaded from a CDN, so the *browser* needs internet for the styling and chart. All data and logic stay local. Vendoring these files for fully-offline use is in "next steps".

## 4. Tech stack and why

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3 + Flask | Small, easy to read, quick to run locally |
| Database | SQLite (`sqlite3`, plain SQL) | Zero setup; one file; a good fit for one shop with ~80 customers. No ORM, so every query is visible and scoped by `user_id` |
| Frontend | Server-rendered Jinja templates, Bootstrap 5, a little JavaScript, Chart.js | No build step; works well on phones; fewer moving parts to break |
| Security | Werkzeug password hashing, Flask-WTF CSRF, session login, parameterised SQL | Standard, well-tested tools |

## 5. Run it locally (about 5 minutes)

You need Python 3.8+.

```bash
# 1. Go into the project folder
cd shop_credit_tracker

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database with demo data
python seed.py

# 5. Start the app
python app.py
```

Open **http://127.0.0.1:5001** (port 5001 is used because macOS AirPlay occupies 5000; change it with `PORT=8000 python app.py`).

**Demo login:** username `demo`, password `demo123` (shop: *Ravi Kirana Store*).

To see it on a real phone on the same Wi-Fi: `HOST=0.0.0.0 python app.py`, then open `http://<your-computer-ip>:5001`. The app listens only on localhost by default.

Run the tests (they use a temporary database and do not touch your demo data):

```bash
python -m unittest discover -s tests
```

Data is stored in `instance/shopkhata.db` and survives refresh, logout and restart. Delete that file and run `python seed.py` to reset.

## 6. Database

```
users                 id, username (unique), password_hash, shop_name, created_at
customers             id, user_id → users, full_name, phone, address, created_at
credit_transactions   id, txn_id (unique), customer_id → customers, user_id → users,
                      description, amount (> 0), txn_date, notes, created_at
payment_transactions  id, txn_id (unique), customer_id → customers, user_id → users,
                      amount (> 0), txn_date, notes, created_at
```

Outstanding balance = `SUM(credit_transactions.amount) − SUM(payment_transactions.amount)`, calculated at query time.

## 7. What I would build next with one more week

1. **Correction entries** and a "void" flag with a reason, instead of editing history.
2. **Shareable statement** per customer (a printable/WhatsApp-able page with the full ledger) as stronger proof in an argument.
3. **Overdue view**: "customers who haven't paid in 30+ days", with one-tap reminders in a row.
4. Store money as integer paise instead of floating-point numbers.
5. Searchable customer picker on the entry screens (better than a drop-down when there are 80+ customers) and quick-amount buttons.
6. Telugu / Hindi labels; install-to-home-screen (PWA); bundle Bootstrap/Chart.js locally for offline use.
7. Rate limiting on login and a password-reset flow.

## 8. Time spent

**TODO – replace with your real number:** approx. __ hours.
