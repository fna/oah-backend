import os
import unittest

import sys
sys.path.append(os.path.join(sys.path[0], '..'))

import utils
from rate_checker import PARAMETERS as params
from county_limit import PARAMETERS as cl_params


class dummy(object):
    def __init__(self, args, path='/rate-checker'):
        self.args = args
        self.path = path


class UtilsTest(unittest.TestCase):

    def test_parse_state_abbr__valid(self):
        """with a valid USA state abbr."""
        result = utils.parse_state_abbr('AL')
        self.assertEquals(result, 'AL')
        result = utils.parse_state_abbr('Ak')
        self.assertEquals(result, 'AK')
        result = utils.parse_state_abbr('az')
        self.assertEquals(result, 'AZ')

    def test_parse_state_abbr__invalid(self):
        """with bad data."""
        self.assertRaises(Exception, utils.parse_state_abbr, 'Alabama')
        self.assertRaises(Exception, utils.parse_state_abbr, 'AM')

    def test_parse_state_name__valid(self):
        """with a valid US state name."""
        result = utils.parse_state_name('VirGiNia')
        self.assertEqual(result, 'VIRGINIA')
        result = utils.parse_state_name('DIStrict oF Columbia')
        self.assertEqual(result, 'DISTRICT OF COLUMBIA')

    def test_parse_state_name__invalid(self):
        """with bad data."""
        self.assertRaises(Exception, utils.parse_state_name, 'Quebec')
        self.assertRaises(Exception, utils.parse_state_name, 'DC')

    def test_parse_str__valid(self):
        """with a string"""
        result = utils.parse_str('TEST')
        self.assertEqual(result, 'TEST')
        result = utils.parse_str(u'TEST')
        self.assertEqual(result, u'TEST')

    def test_parse_str__number(self):
        """with a number"""
        self.assertRaises(Exception, utils.parse_str, 25)
        self.assertRaises(Exception, utils.parse_str, True)

    def test_parse_arm__empty(self):
        """empty arg."""
        self.assertRaises(Exception, utils.parse_arm, '')
        self.assertRaises(Exception, utils.parse_arm, None)

    def test_parse_arm__valid(self):
        """valid value"""
        result = utils.parse_arm('3-1')
        self.assertEqual(result, '3/1')

    def test_parse_arm__invalid(self):
        """invalid value"""
        self.assertRaises(Exception, utils.parse_arm, '3/1')
        self.assertRaises(Exception, utils.parse_arm, '31')
        self.assertRaises(Exception, utils.parse_arm, 31)

    def test_parse_fips__empty(self):
        """empty arg."""
        self.assertRaises(Exception, utils.parse_fips, '')
        self.assertRaises(Exception, utils.parse_fips, None)

    def test_parse_fips__valid(self):
        """valid value"""
        result = utils.parse_fips('02020')
        self.assertEqual(result, '02020')

    def test_parse_fips__invalid(self):
        """invalid value"""
        self.assertRaises(Exception, utils.parse_fips, 'Letters')
        self.assertRaises(Exception, utils.parse_fips, '11222A')
        self.assertRaises(Exception, utils.parse_fips, ' 11222')
        self.assertRaises(Exception, utils.parse_fips, '011222')

    def test_parse_state_fips__empty(self):
        """empty arg."""
        self.assertRaises(Exception, utils.parse_state_fips, '')
        self.assertRaises(Exception, utils.parse_state_fips, None)

    def test_parse_state_fips__valid(self):
        """valid value"""
        result = utils.parse_state_fips('02')
        self.assertEqual(result, '02')

    def test_parse_state_fips__invalid(self):
        """invalid value"""
        self.assertRaises(Exception, utils.parse_state_fips, 'Letters')
        self.assertRaises(Exception, utils.parse_state_fips, '11A')
        self.assertRaises(Exception, utils.parse_state_fips, ' 11')
        self.assertRaises(Exception, utils.parse_state_fips, '011')

    def test_parse_email__empty(self):
        """empty arg"""
        self.assertRaises(Exception, utils.parse_email, '')
        self.assertRaises(Exception, utils.parse_email, None)

    def test_parse_email__valid(self):
        """valid value"""
        result = utils.parse_email('test@example.com')
        self.assertEqual(result, 'test@example.com')
        result = utils.parse_email('te.st@exam.ple.com')
        self.assertEqual(result, 'te.st@exam.ple.com')

    def test_parse_email__invalid(self):
        """invalid value"""
        self.assertRaises(Exception, utils.parse_email, 'test@test@test.com')
        self.assertRaises(Exception, utils.parse_email, 'test@examplecom')
        self.assertRaises(Exception, utils.parse_email, 'test_example.com')

    def test_parse_args__empty(self):
        """with empty args."""
        dummy_request = dummy({})
        result = utils.parse_args(dummy_request, {})
        self.assertTrue('results' in result)
        self.assertEqual(result['results'], {})
        self.assertTrue('errors' in result)
        self.assertEqual(result['errors'], [])

    def test_parse_args__valid(self):
        """with valid args."""
        dummy_request = dummy({'price': 1000, 'downpayment': 10})
        result = utils.parse_args(dummy_request, params)
        self.assertTrue('results' in result)
        self.assertTrue(result['results']['price'], 1000)

    def test_parse_args__invalid(self):
        """with invalid args."""
        dummy_request = dummy({'price': 'Error Message', 'downpayment': 10})
        result = utils.parse_args(dummy_request, params)
        self.assertTrue('results' in result)
        self.assertTrue('price' not in result['results'])
        self.assertTrue('errors' in result)
        self.assertTrue('Error Message' in result['errors'][0])

    def test_check_type__empty(self):
        """with empty value."""
        result = utils.check_type('item_name', None, params)
        self.assertTrue(result is None)

    def test_check_type__valid(self):
        """with valid value."""
        self.assertEqual(utils.check_type('loan_type', 'conf', params), 'conf')
        self.assertEqual(utils.check_type('rate_structure', 'Fixed', params), 'Fixed')
        self.assertEqual(utils.check_type('arm_type', '3-1', params), '3/1')
        self.assertEqual(utils.check_type('loan_term', '111', params), 111)
        self.assertEqual(utils.check_type('loan_term', 114, params), 114)
        self.assertEqual(utils.check_type('price', 20.10, params), 20.10)
        self.assertEqual(utils.check_type('price', '20.20', params), 20.20)
        self.assertEqual(utils.check_type('loan_amount', 19.99, params), 19.99)
        self.assertEqual(utils.check_type('loan_amount', '29.99', params), 29.99)
        self.assertEqual(utils.check_type('state', 'VA', params), 'VA')
        self.assertEqual(utils.check_type('state', 'va', params), 'VA')
        self.assertEqual(utils.check_type('state', 'Va', params), 'VA')
        self.assertEqual(utils.check_type('fico', 100, params), 100)
        self.assertEqual(utils.check_type('fico', '200', params), 200)
        self.assertEqual(utils.check_type('minfico', 300, params), 300)
        self.assertEqual(utils.check_type('minfico', '400', params), 400)
        self.assertEqual(utils.check_type('maxfico', 500, params), 500)
        self.assertEqual(utils.check_type('maxfico', '600', params), 600)

    def test_check_type__invalid(self):
        """with invalid value."""
        self.assertTrue(utils.check_type('loan_type', 11, params) is None)
        self.assertTrue(utils.check_type('rate_structure', 11, params) is None)
        self.assertTrue(utils.check_type('arm_type', 'String', params) is None)
        self.assertTrue(utils.check_type('loan_term', 'A Week', params) is None)
        self.assertTrue(utils.check_type('price', 'String', params) is None)
        self.assertTrue(utils.check_type('loan_amount', 'String', params) is None)
        self.assertTrue(utils.check_type('state', 'Virginia', params) is None)
        self.assertTrue(utils.check_type('fico', 'ABC', params) is None)
        self.assertTrue(utils.check_type('minfico', 'ABC', params) is None)
        self.assertTrue(utils.check_type('maxfico', 'ABC', params) is None)

    def test_execute_query(self):
        """no idea how to do that."""
        pass
