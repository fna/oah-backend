import re


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
        return value.upper()
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

# Serves two purposes: a simple parameters check
# and a white list of accepted parameters

# FIXME fico is not enough, need maxfico and minfico
PARAMETERS = {
    'rate-checker': {
        'downpayment': [
            is_float,
            'Downpayment must be a numeric value, |%s| provided',
            20000,
        ],
        'loan_type': [
            is_str,
            'There was an error processing value |%s| for loan_type parameter',
            '30 year fixed',
        ],
        'price': [
            is_float,
            'House price must be a numeric value, |%s| provided',
            300000,
        ],
        'loan_amount': [
            is_float,
            'Loan amount must be a numeric value, |%s| provided',
            280000,
        ],
        'state': [
            is_state_abbr,
            'State must be a state abbreviation, |%s| provided',
            'DC',
        ],
        'fico': [
            is_int,
            'FICO must be a numeric, |%s| provided',
            720
        ],
        'minfico': [
            is_int,
            'MinFICO must be an integer, |%s| provided',
            600
        ],
        'maxfico': [
            is_int,
            'MaxFICO must be an integer, |%s| provided',
            720
        ]
    },
    'county-limit': {
        'state': [
            is_state_name,
            'State must be a string, |%s| provided',
            'DISTRICT OF COLUMBIA'
        ],
        'county': [
            is_str,
            'County name must be a string, |%s| provided',
            'DISTRICT OF COL'
        ]
    }
}
