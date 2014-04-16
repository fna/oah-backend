STATE_ABBR = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS',
              'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS, MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC',
              'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
              'DC']


def is_state(value):
    """Check that <value> is one of the USA state abbreviations."""
    if value.upper() in STATE_ABBR:
        return value.upper()
    else:
        raise Exception('Not a state abbreviation')


def is_str(value):
    """Check that <value> is a string"""
    if isinstance(value, (unicode, str)):
        return value
    else:
        raise Exception('Not a string')

# Serves two purposes: a simple parameters check
# and a white list of accepted parameters

# FIXME fico is not enough, need maxfico and minfico
PARAMETERS = {
    'downpayment': [
        float,
        'Downpayment must be a numeric value, |%s| provided',
        20000,
    ],
    'loan_type': [
        is_str,
        'There was an error processing value |%s| for loan_type parameter',
        '30 year fixed',
    ],
    'price': [
        float,
        'House price must be a numeric value, |%s| provided',
        300000,
    ],
    'loan_amount': [
        float,
        'Loan amount must be a numeric value, |%s| provided',
        280000,
    ],
    'state': [
        is_state,
        'State must be a state abbreviation, |%s| provided',
        'DC',
    ],
    'fico': [
        int,
        'FICO must be a numeric, |%s| provided',
        720
    ],
    'minfico': [
        int,
        'MinFICO must be an integer, |%s| provided',
        600
    ],
    'maxfico': [
        int,
        'MaxFICO must be an integer, |%s| provided',
        720
    ]
}
