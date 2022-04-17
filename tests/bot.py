import unittest
from unittest import IsolatedAsyncioTestCase

from mmpy_bot import ActionEvent

from em.bot import get_bot


class TestBot(IsolatedAsyncioTestCase):
    emb = get_bot().plugins[0]

    async def test_send_email(self):
        action = ActionEvent(
            request_id='ZWtiem53YzVuYm44cGI2bWJhdWc1aXV6MXI6NWNtbmdpdXpwYmRoZmU2aDFweXdqYzdweXk6MTY1MDIwNzA3ODU5ODpNRVVDSUZJMW1HbkwwM1ljYzV6Ukh3eHF0ZnEvNlNFQlNyWkRUSkJqOGVMS05ubitBaUVBMXlGUFpMMmtTYm1IdkIzbUVXbWhQNWVJb0JkdCtkbDlZS2tmTXBYVEtPMD0=',
            webhook_id='m7k8m6fzijfcff47ekzia9z8cy',
            body={
                'context': {
                    'token': 'token123',
                }
            }
        )
        q = self.emb.driver.response_queue.queue
        self.assertEqual(0, len(q))
        await self.emb.send_email(action)
        self.assertEqual(1, len(q))


if __name__ == '__main__':
    unittest.main()
