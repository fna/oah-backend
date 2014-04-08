import os
import json
import unittest
import tempfile

import sys
sys.path.append(os.path.join(sys.path[0], '..'))

import rate_checker as rc


class RateCheckerTest(unittest.TestCase):

    def setUp(self):
        self.rco = rc.RateChecker()

    def test_is_state__valid(self):
        """with a valid USA state abbr."""
        result = rc.is_state('AL')
        self.assertEquals(result, 'AL')
        result = rc.is_state('Ak')
        self.assertEquals(result, 'AK')
        result = rc.is_state('az')
        self.assertEquals(result, 'AZ')

    def test_is_state__invalid(self):
        """with bad data."""
        self.assertRaises(Exception, rc.is_state, 'Alabama')
        self.assertRaises(Exception, rc.is_state, 'AM')

    def test_process_request(self):
        """trivial check that something's coming back."""
        result = self.rco.process_request({'state': 'VA'})
        self.assertIn('status', result)
        self.assertIsInstance(result['status'], str)
        self.assertIn('errors', result)
        self.assertIsInstance(result['errors'], list)
        self.assertIn('request', result)
        self.assertIsInstance(result['request'], dict)
        self.assertIn('state', result['request'])
        self.assertEquals(result['request']['state'], 'VA')

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

    # TODO: this is our most important function
    def test_get_data(self):
        """_get_data"""
        print "How to initialize test database so we can test this def?"
        pass

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

    def test_clean_args__empty(self):
        """with an empty dict"""
        self.rco._clean_args({})
        self.assertIsInstance(self.rco.request, dict)
        self.assertIn('downpayment', self.rco.request)
        self.assertEqual(self.rco.request['downpayment'], 20000)
        self.assertIn('fico', self.rco.request)
        self.assertEqual(self.rco.request['fico'], 720)
        self.assertIn('loan_amount', self.rco.request)
        self.assertEqual(self.rco.request['loan_amount'], 280000)
        self.assertIn('price', self.rco.request)
        self.assertEqual(self.rco.request['price'], 300000)
        self.assertIn('state', self.rco.request)
        self.assertEqual(self.rco.request['state'], 'DC')

    def test_clean_args__some(self):
        """not all parameters"""
        data = {'downpayment': 10000, 'price': 100000, 'state': 'va'}
        self.rco._clean_args(data)
        result = self.rco.request
        self.assertEqual(result['downpayment'], 10000)
        self.assertEqual(result['price'], 100000)
        self.assertEqual(result['state'], 'VA')
        # weird, but the amount is (re)calculated later process_request function
        self.assertEqual(result['loan_amount'], 280000)
        self.assertEqual(result['loan_type'], '30 year fixed')
        self.assertEqual(result['fico'], 720)

    def test_check_param__na(self):
        """with N/A"""
        result = self.rco._check_param('price', 'N/A')
        self.assertEqual(result, 300000)

    def test_check_param__wrong_type(self):
        """with a wrong data type"""
        result = self.rco._check_param('loan_type', 12)
        self.assertEqual(result, '30 year fixed')

    def test_check_param__ok(self):
        """with a valid value"""
        result = self.rco._check_param('loan_amount', 10)
        self.assertEqual(result, 10)

if __name__ == '__main__':
    unittest.main()
