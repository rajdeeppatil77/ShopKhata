"""
tests/test_audit.py — Comprehensive QA & Security Audit Suite for ShopKhata.
"""
import os
import re
import sys
import unittest
from datetime import datetime

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Isolated test database: never touch instance/shopkhata.db (the demo data) ---
import tempfile
if 'DATABASE_PATH' not in os.environ:
    os.environ['DATABASE_PATH'] = os.path.join(tempfile.mkdtemp(prefix='shopkhata_test_'), 'test.db')

from shopkhata import create_app, get_db, models

if not os.environ.get('_SHOPKHATA_TEST_SEEDED'):
    import seed as _seed
    _seed.seed()
    os.environ['_SHOPKHATA_TEST_SEEDED'] = '1'
from werkzeug.security import check_password_hash


class ShopKhataComprehensiveAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = True

    def setUp(self):
        self.client = self.app.test_client()

    def _extract_csrf(self, html_text):
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html_text)
        self.assertIsNotNone(match, "CSRF token not found in response HTML")
        return match.group(1)

    def _login(self, client, username='demo', password='demo123'):
        page = client.get('/auth/login')
        csrf_token = self._extract_csrf(page.text)
        res = client.post('/auth/login', data={
            'csrf_token': csrf_token,
            'username': username,
            'password': password
        }, follow_redirects=True)
        return res

    # =========================================================================
    # 1. AUTHENTICATION & SECURITY TESTS
    # =========================================================================

    def test_01_unauthenticated_protected_routes(self):
        """Verify all protected routes redirect unauthenticated users to login."""
        protected_urls = ['/', '/customers/', '/transactions/credit/add', '/transactions/payment/add', '/reports/', '/reports/csv']
        for url in protected_urls:
            res = self.client.get(url, follow_redirects=False)
            self.assertEqual(res.status_code, 302, f"Expected 302 redirect for {url}")
            self.assertIn('/auth/login', res.headers['Location'])

    def test_02_csrf_protection_blocks_forged_requests(self):
        """Verify POST requests without CSRF token are blocked with 400 Bad Request."""
        # Attempt login without CSRF token
        res = self.client.post('/auth/login', data={'username': 'demo', 'password': 'demo123'})
        self.assertEqual(res.status_code, 400)

    def test_03_login_failure_with_invalid_credentials(self):
        """Verify invalid login displays error and does not create session."""
        page = self.client.get('/auth/login')
        csrf = self._extract_csrf(page.text)
        res = self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'username': 'demo',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Invalid username or password', res.text)

    def test_04_user_registration_and_password_hashing(self):
        """Verify user registration, validation, password hashing, and clean login."""
        unique_user = f"owner_{int(datetime.now().timestamp())}"
        reg_page = self.client.get('/auth/register')
        csrf = self._extract_csrf(reg_page.text)

        # 4a. Short password rejected
        res = self.client.post('/auth/register', data={
            'csrf_token': csrf,
            'shop_name': 'My Test Shop',
            'username': unique_user,
            'password': '123' # < 6 chars
        }, follow_redirects=True)
        self.assertIn('Password must be at least 6 characters', res.text)

        # 4b. Valid registration
        res = self.client.post('/auth/register', data={
            'csrf_token': csrf,
            'shop_name': 'Super Kirana Store',
            'username': unique_user,
            'password': 'securepassword123'
        }, follow_redirects=True)
        self.assertIn('Account created successfully', res.text)

        # 4c. Verify password in DB is securely hashed
        with self.app.app_context():
            user = models.get_user_by_username(unique_user)
            self.assertIsNotNone(user)
            self.assertNotEqual(user['password_hash'], 'securepassword123')
            self.assertTrue(check_password_hash(user['password_hash'], 'securepassword123'))

        # 4d. Duplicate username rejected
        reg_page2 = self.client.get('/auth/register')
        csrf2 = self._extract_csrf(reg_page2.text)
        res_dup = self.client.post('/auth/register', data={
            'csrf_token': csrf2,
            'shop_name': 'Another Store',
            'username': unique_user,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn('already taken', res_dup.text)

    def test_05_logout_clears_session(self):
        """Verify logging out clears session and prevents access to dashboard."""
        client = self.app.test_client()
        self._login(client)
        # Verify authenticated
        res = client.get('/')
        self.assertEqual(res.status_code, 200)
        # Logout
        res = client.get('/auth/logout', follow_redirects=True)
        self.assertIn('logged out', res.text)
        # Try accessing dashboard again
        res = client.get('/', follow_redirects=False)
        self.assertEqual(res.status_code, 302)

    # =========================================================================
    # 2. MULTI-TENANT USER DATA ISOLATION (SECURITY AUDIT)
    # =========================================================================

    def test_06_strict_multi_tenant_isolation(self):
        """Ensure Shop Owner B cannot view, modify, or record transactions for Shop Owner A."""
        clientA = self.app.test_client()
        clientB = self.app.test_client()

        # Register User A
        ts = int(datetime.now().timestamp())
        userA_name = f"shopA_{ts}"
        userB_name = f"shopB_{ts}"

        p = clientA.get('/auth/register')
        clientA.post('/auth/register', data={
            'csrf_token': self._extract_csrf(p.text),
            'shop_name': 'Shop A',
            'username': userA_name,
            'password': 'password123'
        })
        self._login(clientA, userA_name, 'password123')

        # Register User B
        p = clientB.get('/auth/register')
        clientB.post('/auth/register', data={
            'csrf_token': self._extract_csrf(p.text),
            'shop_name': 'Shop B',
            'username': userB_name,
            'password': 'password123'
        })
        self._login(clientB, userB_name, 'password123')

        # User A creates Customer A
        add_p = clientA.get('/customers/add')
        clientA.post('/customers/add', data={
            'csrf_token': self._extract_csrf(add_p.text),
            'full_name': 'Customer of Shop A',
            'phone': '9811111111',
            'address': 'Street A'
        }, follow_redirects=True)

        with self.app.app_context():
            uA = models.get_user_by_username(userA_name)
            row = get_db().execute("SELECT id FROM customers WHERE full_name='Customer of Shop A' AND user_id=?", (uA['id'],)).fetchone()
            custA_id = row['id']

        # User B attempts to view Customer A's ledger -> MUST 404
        res = clientB.get(f'/customers/{custA_id}')
        self.assertEqual(res.status_code, 404, "Security breach: User B accessed User A customer detail!")

        # User B attempts to edit Customer A -> MUST 404
        res = clientB.get(f'/customers/{custA_id}/edit')
        self.assertEqual(res.status_code, 404, "Security breach: User B accessed User A customer edit!")

        # User B attempts to delete Customer A -> MUST 404
        res = clientB.get(f'/customers/{custA_id}/delete')
        self.assertEqual(res.status_code, 404, "Security breach: User B accessed User A customer delete!")

        # User B attempts to add credit to Customer A -> MUST be blocked
        add_cr_page = clientB.get('/transactions/credit/add')
        res = clientB.post('/transactions/credit/add', data={
            'csrf_token': self._extract_csrf(add_cr_page.text),
            'customer_id': str(custA_id),
            'description': 'Malicious credit injection',
            'amount': '500.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)
        self.assertIn('Selected customer not found in your shop account', res.text)

    # =========================================================================
    # 3. CUSTOMER MANAGEMENT & VALIDATION TESTS
    # =========================================================================

    def test_07_customer_crud_and_validations(self):
        """Test customer creation, phone validation, duplicate handling, edit, and search."""
        client = self.app.test_client()
        self._login(client)

        add_p = client.get('/customers/add')
        csrf = self._extract_csrf(add_p.text)

        # 7a. Empty name rejected
        res = client.post('/customers/add', data={
            'csrf_token': csrf,
            'full_name': '',
            'phone': '9876543210'
        }, follow_redirects=True)
        self.assertIn('Customer full name is required', res.text)

        # 7b. Invalid phone format rejected
        res = client.post('/customers/add', data={
            'csrf_token': csrf,
            'full_name': 'Invalid Phone Guy',
            'phone': '12345' # Not 10 digits
        }, follow_redirects=True)
        self.assertIn('Phone number must be exactly 10 digits', res.text)

        # 7c. Valid customer creation
        cust_name = f"Valid Customer {int(datetime.now().timestamp())}"
        res = client.post('/customers/add', data={
            'csrf_token': csrf,
            'full_name': cust_name,
            'phone': '9988998899',
            'address': 'Plot 42, Civil Lines'
        }, follow_redirects=True)
        self.assertIn('added successfully', res.text)

        # 7d. Duplicate customer handling
        res_dup = client.post('/customers/add', data={
            'csrf_token': csrf,
            'full_name': cust_name,
            'phone': '9988998899',
            'address': 'Plot 42, Civil Lines'
        }, follow_redirects=True)
        self.assertIn('already exists', res_dup.text)

        # 7e. Search customer
        search_res = client.get(f'/customers/?search={cust_name[:12]}')
        self.assertIn(cust_name, search_res.text)

    # =========================================================================
    # 4. CREDIT, PAYMENT & LEDGER MATHEMATICAL ACCURACY
    # =========================================================================

    def test_08_financial_calculations_and_rules(self):
        """Verify:
        - Outstanding Balance = Total Credit - Total Payments
        - Payment > Balance blocked
        - Payment on Zero Balance blocked
        - Negative & Zero credit amounts blocked
        - Customer deletion blocked while balance > 0
        """
        client = self.app.test_client()
        self._login(client)

        # Create customer for financial lifecycle test
        add_p = client.get('/customers/add')
        cust_name = f"Fin Test {int(datetime.now().timestamp())}"
        client.post('/customers/add', data={
            'csrf_token': self._extract_csrf(add_p.text),
            'full_name': cust_name,
            'phone': '9123456789'
        }, follow_redirects=True)

        with self.app.app_context():
            u = models.get_user_by_username('demo')
            row = get_db().execute("SELECT id FROM customers WHERE full_name=? AND user_id=?", (cust_name, u['id'])).fetchone()
            cid = row['id']

        # 8a. Zero balance customer cannot be paid
        pay_p = client.get('/transactions/payment/add')
        res = client.post('/transactions/payment/add', data={
            'csrf_token': self._extract_csrf(pay_p.text),
            'customer_id': str(cid),
            'amount': '100.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)
        self.assertIn('has no outstanding balance', res.text)

        # 8b. Add invalid credit (zero & negative)
        cr_p = client.get('/transactions/credit/add')
        res = client.post('/transactions/credit/add', data={
            'csrf_token': self._extract_csrf(cr_p.text),
            'customer_id': str(cid),
            'description': 'Zero test',
            'amount': '0.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)
        self.assertIn('greater than 0', res.text)

        res = client.post('/transactions/credit/add', data={
            'csrf_token': self._extract_csrf(cr_p.text),
            'customer_id': str(cid),
            'description': 'Negative test',
            'amount': '-150.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)
        self.assertIn('greater than 0', res.text)

        # 8c. Add 1st credit: ₹1,000.00
        client.post('/transactions/credit/add', data={
            'csrf_token': self._extract_csrf(cr_p.text),
            'customer_id': str(cid),
            'description': 'Item Batch 1',
            'amount': '1000.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)

        # 8d. Add 2nd credit: ₹500.00 (Total credit: ₹1,500.00)
        client.post('/transactions/credit/add', data={
            'csrf_token': self._extract_csrf(cr_p.text),
            'customer_id': str(cid),
            'description': 'Item Batch 2',
            'amount': '500.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)

        # Check balance
        with self.app.app_context():
            bal = models.get_customer_balance(cid, u['id'])
            self.assertEqual(bal, 1500.00)

        # 8e. Attempt overpayment: ₹1,501.00 (blocked)
        pay_p = client.get('/transactions/payment/add')
        res = client.post('/transactions/payment/add', data={
            'csrf_token': self._extract_csrf(pay_p.text),
            'customer_id': str(cid),
            'amount': '1501.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)
        self.assertIn('exceeds outstanding balance', res.text)

        # 8f. Record partial payment: ₹600.00 (Remaining balance: ₹900.00)
        client.post('/transactions/payment/add', data={
            'csrf_token': self._extract_csrf(pay_p.text),
            'customer_id': str(cid),
            'amount': '600.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)

        with self.app.app_context():
            bal = models.get_customer_balance(cid, u['id'])
            self.assertEqual(bal, 900.00)

        # 8g. Customer cannot be deleted while balance > 0
        del_p = client.get(f'/customers/{cid}/delete')
        res = client.post(f'/customers/{cid}/delete', data={
            'csrf_token': self._extract_csrf(del_p.text)
        }, follow_redirects=True)
        self.assertIn('Cannot delete customer', res.text)

        # 8h. Pay remaining balance in full: ₹900.00
        client.post('/transactions/payment/add', data={
            'csrf_token': self._extract_csrf(pay_p.text),
            'customer_id': str(cid),
            'amount': '900.00',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)

        with self.app.app_context():
            bal = models.get_customer_balance(cid, u['id'])
            self.assertEqual(bal, 0.00)

        # 8i. Check ledger entries count and running balances
        ledger_res = client.get(f'/customers/{cid}')
        self.assertIn('₹0.00', ledger_res.text)
        self.assertIn('Item Batch 1', ledger_res.text)
        self.assertIn('Item Batch 2', ledger_res.text)
        self.assertIn('Payment Received', ledger_res.text)

        # 8j. Settled customer can now be safely deleted
        del_p = client.get(f'/customers/{cid}/delete')
        res = client.post(f'/customers/{cid}/delete', data={
            'csrf_token': self._extract_csrf(del_p.text)
        }, follow_redirects=True)
        self.assertIn('deleted safely', res.text)

    # =========================================================================
    # 5. DASHBOARD & REPORTS INTEGRITY
    # =========================================================================

    def test_09_dashboard_and_reports_data_accuracy(self):
        """Verify dashboard cards and report totals match exact DB aggregations."""
        client = self.app.test_client()
        self._login(client)

        with self.app.app_context():
            u = models.get_user_by_username('demo')
            stats = models.get_dashboard_stats(u['id'])
            report_data = models.get_report_data(u['id'])

            # Compare calculations
            self.assertEqual(stats['total_credit_given'], report_data['totals']['total_credit'])
            self.assertEqual(stats['total_payments_received'], report_data['totals']['total_paid'])
            self.assertEqual(stats['total_outstanding'], report_data['totals']['total_outstanding'])

        # Verify CSV report stream
        res = client.get('/reports/csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Customer Name', res.text)
        self.assertIn('Outstanding Balance', res.text)
        self.assertIn('TOTALS', res.text)


if __name__ == '__main__':
    unittest.main()
