import unittest
from datetime import datetime

from bluebear.app_pkg.controllers.api.rest_api import TotalBalanceAsOfDate


class TestRestApi(unittest.TestCase):

    def test_parse_moment(self):
        now1 = str(datetime.now().replace(hour=22, minute=0, second=0, microsecond=0))
        now2 = TotalBalanceAsOfDate.parse_moment('now')
        self.assertEqual(now1, now2, f"{now1} != {now2}")

        then1 = str(datetime.now().replace(year=2019, month=6, day=26, hour=22, minute=0, second=0, microsecond=0))

        # https://en.wikipedia.org/wiki/ISO_8601
        then2 = TotalBalanceAsOfDate.parse_moment('2019 - 06 - 26')
        self.assertEqual(then1, then2, f"{then1} != {then2}")

        then2 = TotalBalanceAsOfDate.parse_moment('2019-06-26T04:42:24+00:00')
        self.assertEqual(then1, then2, f"{then1} != {then2}")

        then2 = TotalBalanceAsOfDate.parse_moment('2019-06-26T04:42:24Z')
        self.assertEqual(then1, then2, f"{then1} != {then2}")

        then2 = TotalBalanceAsOfDate.parse_moment('20190626T044224Z')
        self.assertEqual(then1, then2, f"{then1} != {then2}")

    def test_balances_to_json(self):
        balances = {
            1.0: iter([{'base_ccy': 'cc1', 'balance': 10}, {'base_ccy': 'cc2', 'balance': 2000}, ]),
            2.0: iter([{'base_ccy': 'cc2', 'balance': 20}, ]),
            2.1: iter([{'base_ccy': 'cc2', 'balance': 21}, ]),
            3.0: iter([{'base_ccy': 'cc3', 'balance': 30}, ]),
        }

        balances = TotalBalanceAsOfDate.balances_to_map(balances=balances)

        self.assertEqual(balances['cc1'], 10)
        self.assertEqual(balances['cc2'], 41)
        self.assertEqual(balances['cc3'], 30)
