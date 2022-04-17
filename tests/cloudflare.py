import unittest

from em.cloudflare import cf_check_validation, verification_cache, cf_create_email_forward, cf_get_all_verifications


class TestCloudflare(unittest.TestCase):
    def test_email_validation(self):
        cf_get_all_verifications()
        verification_cache['verified'] = {'test1@kix.co.il'}
        verification_cache['unverified'] = {'test2@kix.co.il'}
        self.assertEqual(True, cf_check_validation('test1@kix.co.il'))
        self.assertEqual(False, cf_check_validation('test2@kix.co.il'))
        self.assertEqual(None, cf_check_validation('test3@kix.co.il'))

    def test_create_email(self):
        cf_create_email_forward('test2@kix.co.il', 'test1@kix.co.il')


if __name__ == '__main__':
    unittest.main()
