import re
import os
import oursql


STATE_ABBR = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS',
              'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS, MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC',
              'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
              'DC']

STATE_NAME = ['ALASKA', 'ALABAMA', 'ARKANSAS', 'AMERICAN SAMOA', 'ARIZONA', 'CALIFORNIA', 'COLORADO',
              'CONNECTICUT', 'DISTRICT OF COLUMBIA', 'DELAWARE', 'FLORIDA', 'GEORGIA', 'GUAM', 'HAWAII', 'IOWA',
              'IDAHO', 'ILLINOIS', 'INDIANA', 'KANSAS', 'KENTUCKY', 'LOUISIANA', 'MASSACHUSETTS', 'MARYLAND',
              'MAINE', 'MICHIGAN', 'MINNESOTA', 'MISSOURI', '(NORTHERN) MARIANA ISLANDS', 'MISSISSIPPI', 'MONTANA',
              'NORTH CAROLINA', 'NORTH DAKOTA', 'NEBRASKA', 'NEW HAMPSHIRE', 'NEW JERSEY', 'NEW MEXICO', 'NEVADA',
              'NEW YORK', 'OHIO', 'OKLAHOMA', 'OREGON', 'PENNSYLVANIA', 'PUERTO RICO', 'RHODE ISLAND',
              'SOUTH CAROLINA', 'SOUTH DAKOTA', 'TENNESSEE', 'TEXAS', 'UTAH', 'VIRGINIA', 'VIRGIN ISLANDS',
              'VERMONT', 'WASHINGTON', 'WISCONSIN', 'WEST VIRGINIA', 'WYOMING', ]

errors = []


def is_state_abbr(value):
    """Check that <value> is one of the USA state abbreviations."""
    if value.upper() in STATE_ABBR:
        return value.upper()
    else:
        raise Exception('Not a state abbreviation')


def is_state_name(value):
    """Check that <value> is one of the USA states."""
    if value.upper() in STATE_NAME:
        return value.upper()
    else:
        raise Exception('Not a state name')


def is_str(value):
    """Check that <value> is a string"""
    if isinstance(value, (unicode, str)):
        return value
    else:
        raise Exception('Not a string')


def is_float(value):
    if re.match('^[0-9\.]+$', str(value)):
        return float(value)
    raise Exception('Not a float')


def is_int(value):
    if re.match('^[0-9]+$', str(value)):
        return int(value)
    raise Exception('Not an integer')


def is_arm(value):
    if re.match('^[0-9]{1,2}-1$', str(value)):
        return str(value).replace('-', '/')
    raise Exception('Not an ARM type')


def is_fips(value):
    if re.match('^[0-9]{5}$', str(value)):
        return value
    raise Exception('Not a fips')


def is_state_fips(value):
    if re.match('^[0-9]{2}$', str(value)):
        return value
    raise Exception('Not a fips')


def is_email(value):
    """ very basic check """
    if re.match('^[^@]+@[^@]+\.[^@]+$', str(value)):
        return value
    raise Exception('Not an email address')


def parse_args(request, PARAMETERS):
    """Parse API arguments"""
    global errors
    errors = []
    args = request.args
    params = {}
    for param in PARAMETERS.keys():
        params[param] = check_type(param, args.get(param, None), PARAMETERS)

    return {
        'results': dict((k, v) for k, v in params.iteritems() if v is not None),
        'errors': errors
    }


def check_type(param, value, PARAMETERS):
    """Check type of the value."""
    if value is None:
        return None
    try:
        return PARAMETERS[param][0](value)
    except:
        errors.append(PARAMETERS[param][1] % value)
        return None


def execute_query(query, query_args=None, options=None):
    """Execute query."""
    try:
        dbname = os.environ.get('OAH_DB_NAME', 'dbname')
        dbhost = os.environ.get('OAH_DB_HOST', 'localhost')
        dbuser = os.environ.get('OAH_DB_USER', 'dbuser')
        dbpass = os.environ.get('OAH_DB_PASS', 'password')
        conn = oursql.connect(
            host=dbhost, user=dbuser, passwd=dbpass, db=dbname)
        if options is not None:
            cur = conn.cursor(options)
        else:
            cur = conn.cursor()
        cur.execute(query, query_args)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data
    except Exception as e:
        return "Exception: %s" % e
