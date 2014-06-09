from flask import Flask, request, jsonify, make_response
from flask.ext.mail import Mail

from rate_checker import RateChecker
from county_limit import CountyLimit
from feedback import Feedback

app = Flask('OaH Backend')
app.config.from_envvar('OAH_SETTINGS')

mail = Mail(app)


@app.route('/')
def index():
    return " Request Args: %s " % request.args


@app.route('/rate-checker')
def rate_checker():
    rc = RateChecker()
    resp = make_response(jsonify(**rc.process_request(request)))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/county-limit')
@app.route('/county-limit/list')
def county_limit():
    rc = CountyLimit()
    resp = make_response(jsonify(**rc.process_request(request)))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/feedback', methods=['POST'])
def feedback():
    fb = Feedback(mail=mail)
    resp = make_response(jsonify(**fb.process_request(request)))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)
