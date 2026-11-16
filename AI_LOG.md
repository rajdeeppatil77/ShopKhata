# AI Development Log – ShopKhata

## AI Tools Used

| Tool | Role |
|---|---|
| **Antigravity** (Google DeepMind) | Primary AI development assistant — architecture, scaffolding, and full-stack coding |
| **Model** | Claude Sonnet 4.6 (Thinking) & Gemini 3.8 Flash (Medium) |

---

## Key Prompts Used

**Prompt 1 — Full Project Architecture & Requirements:**
> *"Act as a senior full-stack developer and UI/UX designer. Build a complete, professional, mobile-responsive web application named ShopKhata – Smart Shop Credit Tracker designed for small grocery shop owners who sell products on credit (Khata)... Technology stack: Flask, SQLite, Bootstrap 5, Chart.js..."*

**Prompt 2 — Database Schema & Balance Logic:**
> *"Create SQLite tables for Users, Customers, Credit Transactions, Payment Transactions. Calculate customer balances from their transaction records instead of manually maintaining duplicate balances."*

**Prompt 3 — Fast 5-10 Second Shop Owner Workflow:**
> *"The shop owner must be able to record a credit transaction in approximately 5–10 seconds. Provide Quick Credit, Quick Payment, customer search, large mobile-friendly buttons, and minimal form fields."*

**Prompt 4 — Payment Reminders & Ledgers:**
> *"Generate individual customer ledgers with running balances and unique transaction IDs. Include WhatsApp click-to-chat reminders with personalized Hindi/English text and customer balance."*

---

## Actual AI Mistakes & Corrections Encountered

### Mistake 1: Transaction ID collision in tight loop (`seed.py`)
- **What AI did wrong:** The AI generated transaction IDs using `'PAY' + datetime.now().strftime('%Y%m%d%H%M%S') + rand4()`. In tight automated seed loops, multiple transactions were generated within the same second, resulting in `sqlite3.IntegrityError: UNIQUE constraint failed: payment_transactions.txn_id`.
- **How it was detected:** Executing `python seed.py` failed during database population with an `IntegrityError`.
- **Correction made:** Upgraded the ID generation logic to combine an incremental sequence counter with randomized entropy (`f"{_counter:04d}" + random_digits`) to guarantee 100% uniqueness.

### Mistake 2: SQLite UNION ALL ORDER BY column ambiguity
- **What AI did wrong:** In `get_recent_transactions()`, the AI combined `credit_transactions` and `payment_transactions` using `UNION ALL` and appended `ORDER BY txn_date DESC, created_at DESC`. In SQLite, `created_at` in the second compound query triggered `sqlite3.OperationalError: 2nd ORDER BY term does not match any column in the result set`.
- **How it was detected:** End-to-end automated testing caught an HTTP 500 error on the dashboard route when querying recent transactions.
- **Correction made:** Wrapped the `UNION ALL` compound query inside a subquery `SELECT * FROM (SELECT ... UNION ALL SELECT ...) ORDER BY txn_date DESC, created_at DESC LIMIT ?`.

### Mistake 3: Unregistered `csrf_token` in Jinja context
- **What AI did wrong:** The template included `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />`, but `CSRFProtect(app)` had not been initialized in the Flask factory `__init__.py`, causing a Jinja2 crash: `jinja2.exceptions.UndefinedError: 'csrf_token' is undefined`.
- **How it was detected:** Executing a GET request to `/auth/login` threw a 500 server error during automated unit testing.
- **Correction made:** Initialized `csrf = CSRFProtect(app)` in `shopkhata/__init__.py` and ensured all form templates systematically pass the CSRF token.

---

## Decision Where I Disagreed With AI

- **AI's Suggestion:** The AI initially proposed storing an `outstanding_balance` column directly inside the `customers` table and updating it using manual increments/decrements whenever a credit or payment was added.
- **My Decision:** Rejected manual duplicate balance storage in favor of dynamic aggregation `COALESCE(SUM(credit)) - COALESCE(SUM(payment))` computed directly from immutable ledger transactions.
- **Reason:** In financial software, storing redundant mutable balances inevitably leads to race conditions, partial write desynchronization, and customer disputes. Computing balances directly from the transaction audit log guarantees mathematical consistency and tamper-proof financial integrity.

---

## Developer Verification Notes
- All routes, database queries, and templates were validated using a 12-step end-to-end automated test suite.
- Mobile responsiveness and tap targets were verified for small smartphone screens.
- Zero external ORM dependencies were used, preserving lightweight and transparent SQL execution.
