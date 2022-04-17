import unittest

from em.bot import get_bot
from em.mmapi import send_message


class TestMattermostAPI(unittest.TestCase):
    bot = get_bot()

    def test_send_message(self):
        user_id = 'jxs5xm3b37djjfqohbtp4urpho'
        message = "I've matched token123@nix.co.il with your account.\n" \
                  "Next, click the button at the bottom of this message to get a verification email from cloudflare.\n" \
                  "You will only be sent a single email per address. You must complete verification to receive emails."
        actions = [
            {
                'id': 'hooks',
                'name': 'aaa',
                'integration': {
                    'url': 'http://email-manager.web.svc/hooks/send_email',
                    'context': {
                        'token': 'token123',
                    }
                }
            }
        ]
        result = send_message(self.bot.driver, user_id, message, actions)

        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
