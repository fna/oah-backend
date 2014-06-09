import os
import unittest
from mock import MagicMock, patch

import sys
sys.path.append(os.path.join(sys.path[0], '..'))

import socket

from feedback import Feedback


class dummy(object):
    def __init__(self, name="Name", email="test@example.com", feedback="Feedback"):
        self.form = {
            'name': name,
            'email': email,
            'feedback': feedback
        }


class FeedbackTest(unittest.TestCase):

    def setUp(self):
        self.fb = Feedback()

    def test_process_request__empty(self):
        """with an empty request"""
        data = dummy(None, None, None)
        data.form = {}
        result = self.fb.process_request(data)
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('status' in result)
        self.assertEqual(result['status'], 'Error')
        self.assertTrue('data' in result)
        self.assertTrue(result['data'], 'No email was sent.')

    def test_process_request__incomplete(self):
        """with incomplete data"""
        result = self.fb.process_request(dummy(name=None))
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('status' in result)
        self.assertEqual(result['status'], 'Error')
        self.assertTrue('data' in result)
        self.assertTrue(result['data'], 'No email was sent.')
        self.assertTrue('errors' in result)
        self.assertTrue('Not all required fields were found.' in result['errors'])

    def test_process_request__bademail(self):
        """with bad email address"""
        result = self.fb.process_request(dummy(email='test@example'))
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('status' in result)
        self.assertEqual(result['status'], 'Error')
        self.assertTrue('data' in result)
        self.assertTrue(result['data'], 'No email was sent.')
        self.assertTrue('errors' in result)
        self.assertTrue('|test@example| is not a valid email address.' in result['errors'])

    @patch('feedback.Feedback._send_feedback')
    def test_process_request__valid(self, mock_send_feedback):
        """all data is correct"""

        def update_self():
            self.fb.status = 'OK'
            self.fb.data = 'Email was successfully sent.'

        mock_send_feedback.side_effect = update_self
        result = self.fb.process_request(dummy())
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('status' in result)
        self.assertEqual(result['status'], 'OK')
        self.assertTrue('data' in result)
        self.assertTrue(result['data'], 'Email was successfully sent.')

    def test_send_feedback__nomail(self):
        """mail attr is None"""
        self.fb.mail = None
        result = self.fb._send_feedback()
        self.assertFalse(result)
        self.assertTrue(hasattr(self.fb, 'errors'))
        self.assertTrue('Mail object was not found. Cannot send mails out.' in getattr(self.fb, 'errors'))

    def test_send_feedback__witherrors(self):
        """ with some pre-existent errors"""
        self.fb.mail = 'dup'
        self.fb.errors.append('An error.')
        result = self.fb._send_feedback()
        self.assertFalse(result)
        self.assertTrue(hasattr(self.fb, 'errors'))
        self.assertTrue('An error.' in getattr(self.fb, 'errors'))

    def test_send_feedback__normal(self):
        """normal execution"""
        mail = dummy()
        mail.send = lambda x: 1
        self.fb.mail = mail
        self.fb.request = {
            'name': mail.form['name'],
            'email': mail.form['email'],
            'feedback': mail.form['feedback'],
        }
        result = self.fb._send_feedback()
        self.assertFalse(result)
        self.assertTrue(hasattr(self.fb, 'status'))
        self.assertTrue('OK' in getattr(self.fb, 'status'))
        self.assertTrue(hasattr(self.fb, 'data'))
        self.assertTrue('Email was successfully sent.' in getattr(self.fb, 'data'))

    def test_send_feedback__smtperror(self):
        """SMTP error"""

        def raise_error(self):
            raise socket.error

        mock = MagicMock()
        mock.send.side_effect = raise_error
        self.fb.mail = mock
        self.fb.request = {
            'name': 'Name',
            'email': 'test@example.com',
            'feedback': 'Feedback',
        }
        result = self.fb._send_feedback()
        self.assertFalse(result)
        self.assertTrue(hasattr(self.fb, 'errors'))
        self.assertTrue('Could not connect to SMTP server.' in getattr(self.fb, 'errors'))
        self.assertTrue(hasattr(self.fb, 'status'))
        self.assertTrue('Error' in getattr(self.fb, 'status'))

    def test_output(self):
        result = self.fb._output()
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('status' in result)
        self.assertEquals(result['status'], 'Error')
        self.assertTrue('request' in result)
        self.assertEquals(result['request'], {})
        self.assertTrue('data' in result)
        self.assertEquals(result['data'], 'No email was sent.')
        self.assertTrue('errors' in result)
        self.assertEquals(result['errors'], [])
