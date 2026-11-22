"""
tests/test_security_and_edge_cases.py — Deep Security & Boundary Testing for ShopKhata.
"""
import os
import re
import sys
import unittest
from datetime import datetime

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


class SecurityAndEdgeCasesTest(unittest.TestCase):
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
        return client.post('/auth/login', data={
            'csrf_token': csrf_token,
            'username': username,
            'password': password
        }, follow_redirects=True)

    # =========================================================================
    # 1. SQL INJECTION AUDIT
    # =========================================================================

    def test_sql_injection_resilience(self):
        """Test SQL injection payloads in search, login, and URL parameters."""
        client = self.app.test_client()

        # SQL injection in login
        p = client.get('/auth/login')
        csrf = self._extract_csrf(p.text)
        sqli_payload = "' OR '1'='1' --"
        res = client.post('/auth/login', data={
            'csrf_token': csrf,
            'username': sqli_payload,
            'password': "' OR '1'='1"
        }, follow_redirects=True)
        self.assertIn('Invalid username or password', res.text)

        # Login with valid demo credentials
        self._login(client)

        # SQL injection in customer search
        search_res = client.get(f"/customers/?search={sqli_payload}")
        self.assertEqual(search_res.status_code, 200)

        # SQL injection in customer ID URL
        res = client.get(f"/customers/1%20OR%201=1")
        # Flask routing expects <int:id>, so a non-integer URL fails with 404
        self.assertEqual(res.status_code, 404)

    # =========================================================================
    # 2. XSS (CROSS-SITE SCRIPTING) PREVENTION
    # =========================================================================

    def test_xss_auto_escaping(self):
        """Ensure malicious HTML/JS payloads in customer names and notes are escaped."""
        client = self.app.test_client()
        self._login(client)

        add_p = client.get('/customers/add')
        csrf = self._extract_csrf(add_p.text)
        xss_payload = "<script>alert('xss')</script>"
        xss_name = f"Hacker {int(datetime.now().timestamp())} {xss_payload}"

        client.post('/customers/add', data={
            'csrf_token': csrf,
            'full_name': xss_name,
            'phone': '9876543210',
            'address': '<b>Evil Address</b>'
        }, follow_redirects=True)

        # View directory
        res = client.get('/customers/')
        # Payload must be escaped, NOT present as raw script tag
        self.assertNotIn("<script>alert('xss')</script>", res.text)
        self.assertIn("&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;", res.text)

    # =========================================================================
    # 3. UNICODE & REGIONAL LANGUAGE HANDLING
    # =========================================================================

    def test_hindi_unicode_customer_names(self):
        """Test Indian regional language characters (Hindi / Devanagari) support."""
        client = self.app.test_client()
        self._login(client)

        add_p = client.get('/customers/add')
        csrf = self._extract_csrf(add_p.text)
        hindi_name = f"सुरेश कुमार गुप्ता {int(datetime.now().timestamp())}"

        res = client.post('/customers/add', data={
            'csrf_token': csrf,
            'full_name': hindi_name,
            'phone': '9812300000',
            'address': 'दुकान नंबर ४, पुराना बाज़ार'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Search in Hindi
        search_res = client.get(f"/customers/?search=सुरेश")
        self.assertIn("सुरेश", search_res.text)

    # =========================================================================
    # 4. BOUNDARY VALUE TESTING
    # =========================================================================

    def test_fractional_paise_and_extreme_amounts(self):
        """Verify 2-decimal precision (paise) and boundary amounts."""
        client = self.app.test_client()
        self._login(client)

        # Create customer
        add_p = client.get('/customers/add')
        name = f"Fractional Customer {int(datetime.now().timestamp())}"
        client.post('/customers/add', data={
            'csrf_token': self._extract_csrf(add_p.text),
            'full_name': name,
            'phone': '9876512345'
        }, follow_redirects=True)

        with self.app.app_context():
            u = models.get_user_by_username('demo')
            row = get_db().execute("SELECT id FROM customers WHERE full_name=? AND user_id=?", (name, u['id'])).fetchone()
            cid = row['id']

        # Add 1 paisa (₹0.01)
        cr_p = client.get('/transactions/credit/add')
        client.post('/transactions/credit/add', data={
            'csrf_token': self._extract_csrf(cr_p.text),
            'customer_id': str(cid),
            'description': 'Matchbox',
            'amount': '0.01',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)

        with self.app.app_context():
            self.assertEqual(models.get_customer_balance(cid, u['id']), 0.01)

        # Pay 1 paisa (₹0.01)
        pay_p = client.get('/transactions/payment/add')
        client.post('/transactions/payment/add', data={
            'csrf_token': self._extract_csrf(pay_p.text),
            'customer_id': str(cid),
            'amount': '0.01',
            'txn_date': '2026-11-16'
        }, follow_redirects=True)

        with self.app.app_context():
            self.assertEqual(models.get_customer_balance(cid, u['id']), 0.0)


if __name__ == '__main__':
    unittest.main()
