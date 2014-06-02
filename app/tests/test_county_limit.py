import os
import unittest

import sys
sys.path.append(os.path.join(sys.path[0], '..'))

import county_limit as cl
from county_limit import PARAMETERS as params


class dummy(object):
    def __init__(self, args, path='/county-limit'):
        self.args = args
        self.path = path


class CountyLimitTest(unittest.TestCase):

    def setUp(self):
        self.cl = cl.CountyLimit()

    def test_process_request(self):
        """nothing special"""
        dummy_request = dummy({})
        result = self.cl.process_request(dummy_request)
        self.assertTrue('status' in result)
        self.assertTrue(isinstance(result['status'], str))
        self.assertTrue('errors' in result)
        self.assertTrue(isinstance(result['errors'], list))
        self.assertTrue('request' in result)
        self.assertTrue(isinstance(result['request'], dict))
        self.assertTrue('state_fips' in result['request'])
        self.assertEquals(result['request']['state_fips'], params['state_fips'][2])

    def test_output(self):
        """nothing special"""
        self.cl.status = "OK"
        self.cl.request = "Request"
        self.cl.data = "Data"
        self.cl.errors = "Errors"
        result = self.cl._output()
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('status' in result)
        self.assertEquals(result['status'], 'OK')
        self.assertTrue('request' in result)
        self.assertEquals(result['request'], 'Request')
        self.assertTrue('data' in result)
        self.assertEquals(result['data'], 'Data')
        self.assertTrue('errors' in result)
        self.assertEquals(result['errors'], 'Errors')

    def test_county_limit_data(self):
        # not sure how
        pass

    def test_defaults(self):
        self.cl._defaults()
        data = self.cl.request
        self.assertEqual(data['state_fips'], params['state_fips'][2])
