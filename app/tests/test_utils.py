import os
import unittest

import sys
sys.path.append(os.path.join(sys.path[0], '..'))

import utils


class UtilsTest(unittest.TestCase):

    def test_is_state__valid(self):
        """with a valid USA state abbr."""
        result = utils.is_state('AL')
        self.assertEquals(result, 'AL')
        result = utils.is_state('Ak')
        self.assertEquals(result, 'AK')
        result = utils.is_state('az')
        self.assertEquals(result, 'AZ')

    def test_is_state__invalid(self):
        """with bad data."""
        self.assertRaises(Exception, utils.is_state, 'Alabama')
        self.assertRaises(Exception, utils.is_state, 'AM')

    def test_is_str__valid(self):
        """with a string"""
        result = utils.is_str('TEST')
        self.assertEqual(result, 'TEST')
        result = utils.is_str(u'TEST')
        self.assertEqual(result, u'TEST')

    def test_is_str__number(self):
        """with a number"""
        self.assertRaises(Exception, utils.is_str, 25)
        self.assertRaises(Exception, utils.is_str, True)
