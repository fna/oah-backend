import os
import json
import unittest
import tempfile

import sys
sys.path.append(os.path.join(sys.path[0], '..'))

import rate_checker as rc
from rate_checker import PARAMETERS as params


class dummy(object):
    def __init__(self, args, path='/rate-checker'):
        self.args = args
        self.path = path


class RateCheckerTest(unittest.TestCase):

    def setUp(self):
        self.rco = rc.RateChecker()

    def test_output(self):
        """Not much to test here."""
        self.rco.status = "OK"
        self.rco.request = "Request"
        self.rco.data = "Data"
        self.rco.errors = "Errors"
        result = self.rco._output()
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('status' in result)
        self.assertEquals(result['status'], 'OK')
        self.assertTrue('request' in result)
        self.assertEquals(result['request'], 'Request')
        self.assertTrue('data' in result)
        self.assertEquals(result['data'], 'Data')
        self.assertTrue('errors' in result)
        self.assertEquals(result['errors'], 'Errors')

    def test_calculate_results__data(self):
        """Test _calculate_results"""
        data = [
            {'adjvaluep': 0.1, 'r_totalpoints': 0.2, 'adjvaluer': 1, 'r_baserate': 3,
             'r_planid': 111, 'r_lock': 30},
            {'adjvaluep': 0.3, 'r_totalpoints': 0.4, 'adjvaluer': 3, 'r_baserate': 5,
             'r_planid': 111, 'r_lock': 30},
            {'adjvaluep': 0.1, 'r_totalpoints': 0.2, 'adjvaluer': 1, 'r_baserate': 3,
             'r_planid': 112, 'r_lock': 30},
            {'adjvaluep': 0.1, 'r_totalpoints': 0.2, 'adjvaluer': 1, 'r_baserate': 2,
             'r_planid': 112, 'r_lock': 15},
            {'adjvaluep': 0.1, 'r_totalpoints': -0.2, 'adjvaluer': 1, 'r_baserate': 2,
             'r_planid': 113, 'r_lock': 15},
            {'adjvaluep': 0.1, 'r_totalpoints': 0.2, 'adjvaluer': 2, 'r_baserate': 2,
             'r_planid': 113, 'r_lock': 15},
        ]
        self.rco.request['points'] = 0
        result = self.rco._calculate_results(data)
        self.assertTrue(isinstance(result, dict))

        self.assertTrue('4.000' in result)
        self.assertEqual(result['4.000'], 2)
        self.assertTrue('3.000' in result)
        self.assertEqual(result['3.000'], 1)

    def test_defaults__empty(self):
        """Nothing is set in .request."""
        self.rco._defaults()
        data = self.rco.request
        self.assertEqual(data['loan_type'], params['loan_type'][2])
        self.assertEqual(data['rate_structure'], params['rate_structure'][2])
        self.assertEqual(data['loan_term'], params['loan_term'][2])
        self.assertEqual(data['price'], params['price'][2])
        self.assertEqual(data['loan_amount'], params['loan_amount'][2])
        self.assertEqual(data['state'], params['state'][2])
        self.assertEqual(data['minfico'], params['minfico'][2])
        self.assertEqual(data['maxfico'], params['maxfico'][2])
        self.assertTrue('fico' not in data)
        self.assertTrue('arm_type' not in data)

    def test_defaults__set(self):
        """Some fields are set."""
        self.rco.request['state'] = 'VA'
        self.rco._defaults()
        data = self.rco.request
        self.assertEqual(data['loan_type'], params['loan_type'][2])
        self.assertEqual(data['rate_structure'], params['rate_structure'][2])
        self.assertEqual(data['loan_term'], params['loan_term'][2])
        self.assertEqual(data['price'], params['price'][2])
        self.assertEqual(data['loan_amount'], params['loan_amount'][2])
        self.assertTrue(data['state'] == 'VA')
        self.assertEqual(data['minfico'], params['minfico'][2])
        self.assertEqual(data['maxfico'], params['maxfico'][2])
        self.assertTrue('fico' not in data)
        self.assertTrue('arm_type' not in data)

    def test_set_ficos__empty(self):
        """with all values blank."""
        self.rco._set_ficos()
        data = self.rco.request
        self.assertTrue('minfico' not in data)
        self.assertTrue('maxfico' not in data)
        self.assertTrue('fico' not in data)

    def test_set_ficos__fico(self):
        """with fico set."""
        self.rco.request = {'fico': 100}
        self.rco._set_ficos()
        data = self.rco.request
        self.assertEqual(data['minfico'], 100)
        self.assertEqual(data['maxfico'], 100)

    def test_set_ficos__minfico(self):
        """with minfico set."""
        self.rco.request = {'minfico': 200, 'fico': 100}
        self.rco._set_ficos()
        data = self.rco.request
        self.assertEqual(data['minfico'], 200)
        self.assertEqual(data['maxfico'], 200)

    def test_set_ficos__maxfico(self):
        """with minfico set."""
        self.rco.request = {'maxfico': 200, 'fico': 100}
        self.rco._set_ficos()
        data = self.rco.request
        self.assertEqual(data['minfico'], 200)
        self.assertEqual(data['maxfico'], 200)

    def test_set_ficos__both(self):
        """with minfico and maxfico set."""
        self.rco.request = {'minfico': 300, 'maxfico': 200, 'fico': 100}
        self.rco._set_ficos()
        data = self.rco.request
        self.assertEqual(data['minfico'], 200)
        self.assertEqual(data['maxfico'], 299)

    def test_set_loan_amount__empty(self):
        """with blank values."""
        self.rco._set_loan_amount()
        data = self.rco.request
        self.assertEqual(data, {})

    def test_set_loan_amount__loan_amt(self):
        """with loan_amount set."""
        self.rco.request = {'loan_amount': 10}
        self.rco._set_loan_amount()
        data = self.rco.request
        self.assertEqual(data['price'], 11)
        self.assertEqual(data['loan_amount'], 10)

    def test_set_loan_amount__price(self):
        """with price set."""
        self.rco.request = {'price': 20}
        self.rco._set_loan_amount()
        data = self.rco.request
        self.assertEqual(data['price'], 20)
        self.assertEqual(data['loan_amount'], 18)

    def test_set_loan_amount__all(self):
        """all fields set."""
        self.rco.request = {'price': 20, 'loan_amount': 40}
        self.rco._set_loan_amount()
        data = self.rco.request
        self.assertEqual(data['price'], 40)
        self.assertEqual(data['loan_amount'], 20)


if __name__ == '__main__':
    unittest.main()
