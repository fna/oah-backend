from flask import Flask, request, jsonify

from rate_checker import RateChecker

app = Flask('OaH Backend')


@app.route('/')
def index():
    return " Request Args: %s " % request.args


@app.route('/rate-checker')
def rate_checker():
    rc = RateChecker()
    return jsonify(**rc.process_request(request.args))

app.run(debug=True)
