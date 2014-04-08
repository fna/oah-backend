import psycopg2
import psycopg2.extras
import os

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
    if isinstance(value, str):
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
}


class RateChecker(object):
    """No apparent reason."""

    def __init__(self):
        """Set parameters to default values."""
        # don't know yet what those parameters are
        self.errors = []
        self.data = []
        self.status = "OK"
        self.request = {}

    def process_request(self, args):
        """The main function which processes request and returns result back."""
        self._clean_args(args)
        # don't trust users
        self.request['loan_amount'] = self.request['price'] - self.request['downpayment']
        self.loanterm, _, self.pmttype = self.request['loan_type'].split(' ')
        self._get_data()
        return self._output()

    def _output(self):
        """Compile response"""
        return {
            "status": self.status,
            "request": self.request,
            "data": self.data,
            "errors": self.errors,
        }

    def _get_data(self):
        """Calculate results."""
        data = []
        minltv = 720
        maxltv = 0

        qry_args = [self.request['loan_amount'], self.request['loan_amount'], self.request['fico'],
                    self.request['fico'], minltv, maxltv, self.request['state'], self.request['loan_amount'],
                    self.request['loan_amount'], self.request['fico'], self.request['fico'], minltv, maxltv,
                    self.request['state'], minltv, maxltv, self.request['fico'], self.request['fico'],
                    self.request['loan_amount'], self.request['loan_amount'], self.request['state'],
                    self.pmttype.upper(), self.loanterm]

        query = """
            SELECT
                r.Institution AS r_Institution,
--                r.StateID AS r_StateID,
--                r.LoanPurpose AS r_LoanPurpose,
--                r.PmtType AS r_PmtType,
--                r.LoanType AS r_LoanType,
--                r.LoanTerm AS r_LoanTerm,
--                r.IntAdjTerm AS r_IntAdjTerm,
                r.Lock AS r_Lock,
                r.BaseRate AS r_BaseRate,
                r.TotalPoints AS r_TotalPoints,
--                r.IO AS r_IO,
--                r.OffersAgency AS r_OffersAgency,
                r.Planid AS r_Planid,
--                r.ARMIndex AS r_ARMIndex,
--                r.InterestRateAdjustmentCap AS r_InterestRateAdjustmentCap,
--                r.AnnualCap AS r_AnnualCap,
--                r.LoanCap AS r_LoanCap,
--                r.ARMMargin AS r_ARMMargin,
--                r.AIValue AS r_AIValue,
--                l.Planid AS l_Planid,
--                l.MinLTV AS l_MinLTV,
--                l.MaxLTV AS l_MaxLTV,
--                l.MinFICO AS l_MinFICO,
--                l.MaxFICO AS l_MaxFICO,
--                l.MinLoanAmt AS l_MinLoanAmt,
--                l.MaxLoanAmt AS l_MaxLoanAmt,
                COALESCE(adjr.adjvalueR,0) AS adjvalueR,
                COALESCE(adjp.adjvalueP,0) AS adjvalueP
            FROM
                rates r
                INNER JOIN limits l ON r.planid = l.planid
                LEFT OUTER JOIN (
                    SELECT
                        planid,
                        sum(adjvalue) adjvalueR
                    FROM adjustments
                    WHERE
                        MINLOANAMT <= %s AND %s <= MAXLOANAMT
                        AND MINFICO<= %s AND MAXFICO >= %s
                        AND %s >= minltv AND %s <= maxltv
                        -- AND proptype=''
                        AND (STATE=%s or STATE = '')
                        -- AND AffectRateType='R'
                    GROUP BY planid
                )  adjr ON adjr.PlanID = r.planid
                LEFT OUTER JOIN (
                    SELECT
                        planid,
                        sum(adjvalue) adjvalueP
                    FROM adjustments
                    WHERE
                        MINLOANAMT <= %s AND %s <= MAXLOANAMT
                        AND MINFICO<= %s AND MAXFICO >= %s
                        AND %s >= minltv AND %s <= maxltv
                        -- AND proptype=''
                        AND (STATE=%s or STATE = '')
                        -- AND AffectRateType='P'
                    GROUP BY planid
                )  adjp ON adjp.PlanID = r.planid

            WHERE 1=1
                -- Limits stuff
                AND (l.minltv <= %s AND l.maxltv >= %s)
                AND (l.minfico <= %s AND l.maxfico >= %s)
                AND (l.minloanamt <= %s AND l.maxloanamt >= %s)
                AND (r.stateid=%s or r.stateid='')
                -- AND r.loanpurpose='PURCH'
                AND r.pmttype=%s
                -- AND r.loantype='CONF'
                AND r.loanterm=%s

            ORDER BY r_Institution, r_BaseRate
        """
        try:
            dbname = os.environ.get('OAH_DB_NAME', 'pg_test')
            dbhost = os.environ.get('OAH_DB_HOST', 'localhost')
            conn = psycopg2.connect('dbname=%s host=%s' % (dbname, dbhost))
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query, qry_args)
            self.data = self._calculate_results(cur.fetchall())
            cur.close()
            conn.close()
        except Exception as e:
            return "Exception %s" % e

    def _calculate_results(self, data):
        """Remove extra rows. Return rates with numbers."""
        result = {}
        for row in data:
            row['final_points'] = row['adjvaluep'] + row['r_totalpoints']
            row['final_rates'] = row['adjvaluer'] + row['r_baserate']
            if (
                row['r_planid'] not in result or
                result[row['r_planid']]['r_totalpoints'] > row['r_totalpoints'] or
                (result[row['r_planid']]['r_totalpoints'] == row['r_totalpoints'] and
                 result[row['r_planid']]['r_lock'] > row['r_lock'])
            ):
                result[row['r_planid']] = row
        data = {}
        for row in result.keys():
            if result[row]['final_rates'] in data:
                data[result[row]['final_rates']] += 1
            else:
                data[result[row]['final_rates']] = 1
        return data

    def _clean_args(self, args):
        """Return a dict of args, checked and cleansed."""
        params = {}
        for param in PARAMETERS.keys():
            params[param] = self._check_param(param, args.get(param, 'N/A'))
        self.request = {param: params[param] for param in params if params[param]}

    def _check_param(self, param, value):
        """Plain check of param's type, and setting defaults."""
        if value == 'N/A':
            return PARAMETERS[param][2]
        try:
            return PARAMETERS[param][0](value)
        except:
            self.errors.append(PARAMETERS[param][1] % value)
            self.status = "Error"
            return PARAMETERS[param][2]
