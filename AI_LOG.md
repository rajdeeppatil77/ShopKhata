# AI Development Log – ShopKhata

## AI Tools Used

| Tool | Role |
|---|---|
| **Antigravity** (Google DeepMind) | Primary AI development assistant — architecture, scaffolding, full-stack coding, and QA testing |
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

**Prompt 5 — Comprehensive QA, Security & Reliability Audit:**
> *"Act as a senior Python Flask developer, software tester, QA engineer, database administrator, and security auditor. Thoroughly inspect the existing project, execute the application, test its functionality, identify errors, and fix them."*

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

### Mistake 4: Missing Registration form fields in `login.html`
- **What AI did wrong:** The auth blueprint routed `/auth/register` to `render_template('auth/login.html', register_mode=True)`, but `login.html` was missing the `register_mode` conditional block, preventing new shop owners from creating accounts via the web interface.
- **How it was detected:** During QA inspection, navigating to `/auth/register` rendered only the login inputs without shop name, registration action, or toggle links.
- **Correction made:** Added a dynamic registration form block in `login.html` with business shop name, username, password validation, and toggle links between Login and Register.

### Mistake 5: Floating point IEEE 754 precision discrepancy in aggregations
- **What AI did wrong:** Dashboard queried SQLite `SUM()` while Reports summed Python float list elements (`sum(c['total_credit'] for c in balances)`), causing an unrounded binary float drift (`12257.95 != 12257.949999999999`).
- **How it was detected:** Detected during the mathematical equality test between dashboard metrics and financial report aggregations.
- **Correction made:** Enforced `round(..., 2)` on all financial currency totals across both SQL queries and reporting aggregations.

### Mistake 6: Missing cross-tenant ownership check in transaction insertion
- **What AI did wrong:** `add_credit` and `add_payment` accepted `customer_id` and `user_id` without verifying that the customer actually belonged to that specific shop owner, which could allow malicious users to inject transactions onto other shops' customers.
- **How it was detected:** Multi-tenant security audit test revealed that an unauthorized user could pass another store's `customer_id`.
- **Correction made:** Added strict ownership verification (`customer = models.get_customer(customer_id, user_id)`) before permitting any credit or payment transaction.

---

## Decision Where I Disagreed With AI

- **AI's Suggestion:** The AI initially proposed storing an `outstanding_balance` column directly inside the `customers` table and updating it using manual increments/decrements whenever a credit or payment was added.
- **My Decision:** Rejected manual duplicate balance storage in favor of dynamic aggregation `COALESCE(SUM(credit)) - COALESCE(SUM(payment))` computed directly from immutable ledger transactions.
- **Reason:** In financial software, storing redundant mutable balances inevitably leads to race conditions, partial write desynchronization, and customer disputes. Computing balances directly from the transaction audit log guarantees mathematical consistency and tamper-proof financial integrity.

---

## Developer Verification Notes
- Tested across desktop and mobile viewport resolutions with Bootstrap 5 responsive grid and off-canvas sidebar.
- 13 automated unit, integration, and security tests in `tests/` pass with zero failures.
- Zero external ORM dependencies; clean parameterized SQLite queries ensure fast, auditable execution.
