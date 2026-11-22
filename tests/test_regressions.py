"""Regression tests for bugs found during the assignment review."""
import os
import re
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if 'DATABASE_PATH' not in os.environ:
    os.environ['DATABASE_PATH'] = os.path.join(tempfile.mkdtemp(prefix='shopkhata_test_'), 'test.db')

from shopkhata import create_app, models
if not os.environ.get('_SHOPKHATA_TEST_SEEDED'):
    import seed as _seed
    _seed.seed()
    os.environ['_SHOPKHATA_TEST_SEEDED'] = '1'


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True

    def setUp(self):
        self.client = self.app.test_client()

    def _csrf(self, html):
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
        self.assertIsNotNone(m)
        return m.group(1)

    def _login(self, next_url=None):
        url = '/auth/login' + (f'?next={next_url}' if next_url else '')
        page = self.client.get(url)
        return self.client.post(url, data={
            'csrf_token': self._csrf(page.text), 'username': 'demo', 'password': 'demo123'})

    def _first_customer_with_balance(self):
        with self.app.app_context():
            rows = models.get_customers_with_balance(1)
            return next(c for c in rows if c['balance'] > 1)

    def _post(self, path, data):
        page = self.client.get(path)
        data = dict(data, csrf_token=self._csrf(page.text))
        return self.client.post(path, data=data)

    def test_open_redirect_blocked(self):
        for bad in ('//evil.com', '/\\evil.com', 'http://evil.com'):
            res = self._login(bad)
            self.assertEqual(res.status_code, 302)
            self.assertNotIn('evil.com', res.headers['Location'])

    def test_next_redirect_works_for_local_path(self):
        res = self.client.get('/customers/')
        self.assertRegex(res.headers['Location'], r'next=(/|%2F)customers')
        res = self._login('/customers/')
        self.assertTrue(res.headers['Location'].endswith('/customers/'))

    def test_credit_needs_only_customer_and_amount(self):
        self._login()
        c = self._first_customer_with_balance()
        before = c['balance']
        res = self._post('/transactions/credit/add', {'customer_id': c['id'], 'amount': '50'})
        self.assertEqual(res.status_code, 302)
        with self.app.app_context():
            self.assertAlmostEqual(models.get_customer_balance(c['id'], 1), before + 50, places=2)

    def test_bad_amounts_never_cause_500(self):
        self._login()
        c = self._first_customer_with_balance()
        for path in ('/transactions/credit/add', '/transactions/payment/add'):
            for amt in ('', 'nan', 'inf', '-5', '0', 'abc', '1e12'):
                res = self._post(path, {'customer_id': c['id'], 'amount': amt})
                self.assertEqual(res.status_code, 200, f'{path} amount={amt!r}')

    def test_invalid_date_rejected(self):
        self._login()
        c = self._first_customer_with_balance()
        res = self._post('/transactions/credit/add',
                         {'customer_id': c['id'], 'amount': '10', 'txn_date': 'not-a-date'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('Date is not valid', res.text)


if __name__ == '__main__':
    unittest.main()
