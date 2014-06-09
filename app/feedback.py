from utils import is_email
from flask.ext.mail import Message

import errno
import socket
import os


class Feedback(object):

    def __init__(self, mail=None):
        self.data = "No email was sent."
        self.errors = []
        self.status = "Error"
        self.request = {}
        self.mail = mail
        try:
            oah_feedback_to = os.environ['OAH_FEEDBACK_TO']
        except KeyError as e:
            self.errors.append('OAH_FEEDBACK_TO was not set.')
            oah_feedback_to = ''
        self.oah_feedback_to = oah_feedback_to.split(',')

    def process_request(self, request):
        """The main function which sends feedback and returns status back."""
        if request.form:
            data = request.form
            self.request['email'], self.request['name'], self.request['feedback'] = [data.get('email', ''), data.get('name', ''), data.get('feedback', '')]
            if not self.request['email'] or not self.request['name'] or not self.request['feedback']:
                self.errors.append('Not all required fields were found.')

            try:
                is_email(self.request['email'])
            except Exception:
                self.errors.append('|%s| is not a valid email address.' % self.request['email'])

        self._send_feedback()
        return self._output()

    def _send_feedback(self):
        """."""
        if not self.mail:
            self.errors.append('Mail object was not found. Cannot send mails out.')
        if self.errors:
            return

        try:
            msg = Message("Feedback for OaH", sender="test@example.com", recipients=self.oah_feedback_to)
            msg.body = "By: %s <%s>\n\n%s" % (self.request['name'], self.request['email'], self.request['feedback'])
            self.mail.send(msg)
            self.data = 'Email was successfully sent.'
            self.status = 'OK'
        except socket.error:
            self.errors.append('Could not connect to SMTP server.')

    def _output(self):
        """."""
        return {
            "data": self.data,
            "request": self.request,
            "status": self.status,
            "errors": self.errors
        }
