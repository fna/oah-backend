from flask import Flask, request, jsonify, make_response

from rate_checker import RateChecker
from county_limit import CountyLimit

app = Flask('OaH Backend')


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
def county_limit():
    rc = CountyLimit()
    resp = make_response(jsonify(**rc.process_request(request)))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)
