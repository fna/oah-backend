import os
import json
import unittest
import tempfile

import sys
sys.path.append(os.path.join(sys.path[0], '..'))

import rate_checker as rc
from utils import PARAMETERS as params


class dummy(object):
    def __init__(self, args, path='/rate-checker'):
        self.args = args
        self.path = path


class RateCheckerTest(unittest.TestCase):

    def setUp(self):
        self.rco = rc.RateChecker()

    def test_process_request(self):
        """trivial check that something's coming back."""
        dummy_request = dummy({'state': 'VA'})
        result = self.rco.process_request(dummy_request)
        self.assertIn('status', result)
        self.assertIsInstance(result['status'], str)
        self.assertIn('errors', result)
        self.assertIsInstance(result['errors'], list)
        self.assertIn('request', result)
        self.assertIsInstance(result['request'], dict)
        self.assertIn('state', result['request'])
        self.assertEquals(result['request']['state'], 'VA')

        dummy_request = dummy({}, '/county-limit')
        result = self.rco.process_request(dummy_request)
        self.assertIn('status', result)
        self.assertIsInstance(result['status'], str)
        self.assertIn('errors', result)
        self.assertIsInstance(result['errors'], list)
        self.assertIn('request', result)
        self.assertIsInstance(result['request'], dict)
        self.assertIn('state', result['request'])
        self.assertEquals(result['request']['state'], 'DISTRICT OF COLUMBIA')

    def test_output(self):
        """Not much to test here."""
        self.rco.status = "OK"
        self.rco.request = "Request"
        self.rco.data = "Data"
        self.rco.errors = "Errors"
        result = self.rco._output()
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertEquals(result['status'], 'OK')
        self.assertIn('request', result)
        self.assertEquals(result['request'], 'Request')
        self.assertIn('data', result)
        self.assertEquals(result['data'], 'Data')
        self.assertIn('errors', result)
        self.assertEquals(result['errors'], 'Errors')

    def test_get_data(self):
        # is mostly about running the query, so I don't see need to test it.
        pass

    def test_get_county_limit__valid(self):
        """with valid data."""
        self.rco.request = {
            # will probably change, looks like wrong data
            # but this is how it's in db right now
            'county': 'DISTRICT OF COL',
            'state': 'DISTRICT OF COLUMBIA',
        }
        self.rco._get_county_limit()
        self.assertEqual(len(self.rco.data), 1)
        self.assertIn('fha_limit', self.rco.data[0])
        self.assertIn('gse_limit', self.rco.data[0])
        # This might change when we load new data
        self.assertEqual(self.rco.data[0]['fha_limit'], '625500.00')
        self.assertEqual(self.rco.data[0]['gse_limit'], '625500.00')

        self.rco.data = []
        self.rco.request = {
            'county': 'NORTHAMPTON',
            'state': 'VIRGINIA',
        }
        self.rco._get_county_limit()
        self.assertEqual(len(self.rco.data), 1)
        self.assertIn('fha_limit', self.rco.data[0])
        self.assertIn('gse_limit', self.rco.data[0])
        # This might change when we load new data
        self.assertEqual(self.rco.data[0]['fha_limit'], '271050.00')
        self.assertEqual(self.rco.data[0]['gse_limit'], '417000.00')

    def test_get_county_limit__invalid(self):
        """with invalid data."""
        self.rco.request = {
            'county': 'NORTHAMPTON',
        }
        self.rco._get_county_limit()
        self.assertEqual(len(self.rco.data), 0)

        self.rco.request = {
            'state': 'VIRGINIA',
        }
        self.rco._get_county_limit()
        self.assertEqual(len(self.rco.data), 0)

        self.rco.request = {
            'state': 'ViRgINIA',
            'county': 'NORTHAMPTON',
        }
        self.rco._get_county_limit()
        self.assertEqual(len(self.rco.data), 0)

    def test_calculate_results__empty(self):
        """with an empty list"""
        result = self.rco._calculate_results([])
        self.assertEqual(result, {})

    def test_calculate_results__data(self):
        """Test _calculate_results"""
        data = [
            {'adjvaluep': 1, 'r_totalpoints': 2, 'adjvaluer': 1, 'r_baserate': 3,
             'r_planid': 111, 'r_lock': 30},
            {'adjvaluep': 3, 'r_totalpoints': 4, 'adjvaluer': 3, 'r_baserate': 5,
             'r_planid': 111, 'r_lock': 30},
            {'adjvaluep': 1, 'r_totalpoints': 2, 'adjvaluer': 1, 'r_baserate': 3,
             'r_planid': 112, 'r_lock': 30},
            {'adjvaluep': 1, 'r_totalpoints': 2, 'adjvaluer': 1, 'r_baserate': 2,
             'r_planid': 112, 'r_lock': 15},
            {'adjvaluep': 1, 'r_totalpoints': 2, 'adjvaluer': 1, 'r_baserate': 2,
             'r_planid': 113, 'r_lock': 15},
        ]
        result = self.rco._calculate_results(data)
        self.assertIsInstance(result, dict)
        self.assertIn(4, result)
        self.assertEqual(result[4], 1)
        self.assertIn(3, result)
        self.assertEqual(result[3], 2)

    def test_parse_args__empty(self):
        """with an empty dict"""
        dummy_request = dummy({})
        path = 'rate-checker'
        self.rco._parse_args(dummy_request)
        self.assertIsInstance(self.rco.request, dict)
        self.assertIn('downpayment', self.rco.request)
        self.assertEqual(self.rco.request['downpayment'], params[path]['downpayment'][2])
        self.assertNotIn('fico', self.rco.request)
        self.assertIn('minfico', self.rco.request)
        self.assertEqual(self.rco.request['minfico'], params[path]['minfico'][2])
        self.assertIn('maxfico', self.rco.request)
        self.assertEqual(self.rco.request['maxfico'], params[path]['maxfico'][2])
        self.assertIn('loan_amount', self.rco.request)
        self.assertEqual(self.rco.request['loan_amount'], params[path]['loan_amount'][2])
        self.assertIn('price', self.rco.request)
        self.assertEqual(self.rco.request['price'], params[path]['price'][2])
        self.assertIn('state', self.rco.request)
        self.assertEqual(self.rco.request['state'], params[path]['state'][2])

        dummy_request.path = '/county-limit'
        path = 'county-limit'
        self.rco._parse_args(dummy_request)
        self.assertIsInstance(self.rco.request, dict)
        self.assertIn('county', self.rco.request)
        self.assertEqual(self.rco.request['county'], params[path]['county'][2])
        self.assertIsInstance(self.rco.request, dict)
        self.assertIn('state', self.rco.request)
        self.assertEqual(self.rco.request['state'], params[path]['state'][2])

    def test_parse_args__some(self):
        """not all parameters"""
        dummy_request = dummy({'downpayment': 10000, 'price': 100000, 'state': 'va'})
        path = 'rate-checker'
        self.rco._parse_args(dummy_request)
        result = self.rco.request
        self.assertEqual(result['downpayment'], 10000)
        self.assertEqual(result['price'], 100000)
        self.assertEqual(result['state'], 'VA')
        self.assertEqual(result['loan_amount'], 90000)
        self.assertEqual(result['loan_type'], '30 year fixed')
        self.assertEqual(result['minfico'], params[path]['minfico'][2])
        self.assertEqual(result['maxfico'], params[path]['maxfico'][2])

        dummy_request = dummy({'state': 'VIRGINIA'}, '/county-limit')
        path = 'county-limit'
        self.rco._parse_args(dummy_request)
        result = self.rco.request
        self.assertEqual(result['state'], 'VIRGINIA')
        self.assertEqual(result['county'], params[path]['county'][2])

    def test_parse_args__errors(self):
        """check that errors list is populated."""
        dummy_request = dummy({'downpayment': 'error', 'price': 100000, 'state': 'OO'})
        self.rco._parse_args(dummy_request)
        self.assertIsInstance(self.rco.errors, list)
        self.assertTrue(len(self.rco.errors) == 2)

    def test_check_type__invalid(self):
        """with invalid arg"""
        result = self.rco._check_type('rate-checker', 'downpayment', 'string but not a number')
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'downpayment', True)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'loan_type', True)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'loan_type', 30)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'price', 'string, not a number')
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'price', False)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'loan_amount', 'string, not a number')
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'loan_amount', True)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'state', 30)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'state', True)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'fico', 'string, not a number')
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'fico', True)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'fico', 30.10)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'minfico', 'stirng, not a number')
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'minfico', True)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'minfico', 30.10)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'maxfico', 'string, not a number')
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'maxfico', True)
        self.assertTrue(result is None)
        result = self.rco._check_type('rate-checker', 'maxfico', 30.10)
        self.assertTrue(result is None)

    def test_check_type__valid(self):
        """with valid values"""
        result = self.rco._check_type('rate-checker', 'downpayment', 10)
        self.assertEqual(result, 10.0)
        result = self.rco._check_type('rate-checker', 'downpayment', 10.10)
        self.assertEqual(result, 10.10)
        result = self.rco._check_type('rate-checker', 'loan_type', '30 year fixed')
        self.assertEqual(result, '30 YEAR FIXED')
        result = self.rco._check_type('rate-checker', 'price', '2000')
        self.assertEqual(result, 2000.0)
        result = self.rco._check_type('rate-checker', 'price', 2000)
        self.assertEqual(result, 2000.0)
        result = self.rco._check_type('rate-checker', 'price', 2000.20)
        self.assertEqual(result, 2000.20)
        result = self.rco._check_type('rate-checker', 'loan_amount', '40000.99')
        self.assertEqual(result, 40000.99)
        result = self.rco._check_type('rate-checker', 'loan_amount', 4000)
        self.assertEqual(result, 4000)
        result = self.rco._check_type('rate-checker', 'loan_amount', 4000.99)
        self.assertEqual(result, 4000.99)
        result = self.rco._check_type('rate-checker', 'state', 'va')
        self.assertEqual(result, 'VA')
        result = self.rco._check_type('rate-checker', 'state', 'VA')
        self.assertEqual(result, 'VA')
        result = self.rco._check_type('rate-checker', 'state', 'vA')
        self.assertEqual(result, 'VA')
        result = self.rco._check_type('rate-checker', 'fico', '99')
        self.assertEqual(result, 99)
        result = self.rco._check_type('rate-checker', 'fico', 99)
        self.assertEqual(result, 99)
        result = self.rco._check_type('rate-checker', 'minfico', '99')
        self.assertEqual(result, 99)
        result = self.rco._check_type('rate-checker', 'minfico', 99)
        self.assertEqual(result, 99)
        result = self.rco._check_type('rate-checker', 'maxfico', '99')
        self.assertEqual(result, 99)
        result = self.rco._check_type('rate-checker', 'maxfico', 99)
        self.assertEqual(result, 99)

    def test_set_ficos__empty(self):
        """with all values blank."""
        data = {'minfico': None, 'maxfico': None, 'fico': None}
        self.rco._set_ficos(data)
        self.assertEqual(data['minfico'], None)
        self.assertEqual(data['maxfico'], None)
        self.assertTrue('fico' not in data)

    def test_set_ficos__fico(self):
        """with fico set."""
        data = {'minfico': None, 'maxfico': None, 'fico': 100}
        self.rco._set_ficos(data)
        self.assertEqual(data['minfico'], 100)
        self.assertEqual(data['maxfico'], 100)
        self.assertTrue('fico' not in data)

    def test_set_ficos__minfico(self):
        """with minfico set."""
        data = {'minfico': 200, 'maxfico': None, 'fico': 100}
        self.rco._set_ficos(data)
        self.assertEqual(data['minfico'], 200)
        self.assertEqual(data['maxfico'], 200)
        self.assertTrue('fico' not in data)

    def test_set_ficos__maxfico(self):
        """with minfico set."""
        data = {'minfico': None, 'maxfico': 200, 'fico': 100}
        self.rco._set_ficos(data)
        self.assertEqual(data['minfico'], 200)
        self.assertEqual(data['maxfico'], 200)
        self.assertTrue('fico' not in data)

    def test_set_ficos__both(self):
        """with minfico and maxfico set."""
        data = {'minfico': 300, 'maxfico': 200, 'fico': 100}
        self.rco._set_ficos(data)
        self.assertEqual(data['minfico'], 200)
        self.assertEqual(data['maxfico'], 300)
        self.assertTrue('fico' not in data)

    def test_set_loan_amount__empty(self):
        """with blank values."""
        data = {'price': None, 'loan_amount': None, 'downpayment': None}
        self.rco._set_loan_amount(data, params['rate-checker'])
        self.assertEqual(data['price'], params['rate-checker']['price'][2])
        self.assertEqual(data['downpayment'], params['rate-checker']['downpayment'][2])
        self.assertEqual(data['loan_amount'], params['rate-checker']['loan_amount'][2])

    def test_set_loan_amount__loan_amt(self):
        """with loan_amount set."""
        data = {'price': None, 'loan_amount': 10, 'downpayment': None}
        self.rco._set_loan_amount(data, params['rate-checker'])
        self.assertEqual(data['price'], 10)
        self.assertEqual(data['downpayment'], 0)
        self.assertEqual(data['loan_amount'], 10)

    def test_set_loan_amount__price(self):
        """with price set."""
        data = {'price': 20, 'loan_amount': None, 'downpayment': None}
        self.rco._set_loan_amount(data, params['rate-checker'])
        self.assertEqual(data['price'], 20)
        self.assertEqual(data['downpayment'], 0)
        self.assertEqual(data['loan_amount'], 20)

    def test_set_loan_amount__all(self):
        """all fields set."""
        data = {'price': 20, 'loan_amount': 40, 'downpayment': 10}
        self.rco._set_loan_amount(data, params['rate-checker'])
        self.assertEqual(data['price'], 50)
        self.assertEqual(data['downpayment'], 10)
        self.assertEqual(data['loan_amount'], 40)

    def test_set_loan_amount_downpayment(self):
        """with downpayment set."""
        data = {'price': None, 'loan_amount': None, 'downpayment': 99}
        self.rco._set_loan_amount(data, params['rate-checker'])
        self.assertEqual(data['price'], params['rate-checker']['price'][2])
        self.assertEqual(data['downpayment'], params['rate-checker']['downpayment'][2])
        self.assertEqual(data['loan_amount'], params['rate-checker']['loan_amount'][2])


if __name__ == '__main__':
    unittest.main()
