import oursql
import psycopg2.extras

from utils import (STATE_ABBR, parse_args, execute_query, is_float, is_str, is_arm, is_int, is_state_abbr)

PARAMETERS = {
    'downpayment': [
        is_float,
        'Downpayment must be a numeric value, |%s| provided',
        20000,
    ],
    'loan_type': [
        is_str,
        'There was an error processing value |%s| for loan_type parameter',
        'CONF',
    ],
    'rate_structure': [
        is_str,
        'There was an error processing value |%s| for rate_structure parameter',
        'Fixed',
    ],
    'arm_type': [
        is_arm,
        'The value |%s| does not look like an ARM type parameter',
        '3/1',
    ],
    'loan_term': [
        is_int,
        'Loan term must be a numeric value, |%s| provided',
        30,
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
    ],
    'points': [
        is_float,
        'Points value must be a numeric, |%s| provided',
        1.25
    ],
    'lock': [
        is_int,
        'Lock value must be an integer, |%s| provided',
        60
    ],
    #'property_type': [
    #    is_str,
    #    'There was an error processing |%s| for property type',
    #    'CONDO',
    #]
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

    def process_request(self, request):
        """The main function which processes request and returns result back."""
        results = parse_args(request, PARAMETERS)
        self.request = results['results']
        if len(results['errors']) > 0:
            self.errors = results['errors']
            self.status = 'Error'
        self._defaults()
        self._data()
        return self._output()

    def _output(self):
        """Compile response"""
        return {
            "status": self.status,
            "request": self.request,
            "data": self.data,
            "errors": self.errors,
        }

    def _data(self):
        """Calculate results."""
        data = []
        minltv = maxltv = float(self.request['loan_amount']) / self.request['price'] * 100

        # lock times
        locks = {
            30: [0, 30],
            45: [31, 45],
            60: [46, 60],
        }
        minlock = maxlock = self.request['lock']
        if self.request['lock'] in locks:
            minlock = locks[self.request['lock']][0]
            maxlock = locks[self.request['lock']][1]

        qry_args = [self.request['loan_amount'], self.request['loan_amount'], self.request['minfico'],
                    self.request['maxfico'], minltv, maxltv, self.request['state'], self.request['loan_amount'],
                    self.request['loan_amount'], self.request['minfico'], self.request['maxfico'], minltv, maxltv,
                    self.request['state'], minltv, maxltv, self.request['minfico'], self.request['maxfico'],
                    self.request['loan_amount'], self.request['loan_amount'], self.request['state'],
                    self.request['rate_structure'].upper(), self.request['loan_term'], self.request['loan_type'],
                    minlock, maxlock, self.request['points']]

        query = """
            SELECT
                r.Institution AS r_institution,
--                r.StateID AS r_StateID,
--                r.LoanPurpose AS r_LoanPurpose,
--                r.PmtType AS r_PmtType,
--                r.LoanType AS r_LoanType,
--                r.LoanTerm AS r_LoanTerm,
--                r.IntAdjTerm AS r_IntAdjTerm,
                r.Lock AS r_lock,
                r.BaseRate AS r_baserate,
                r.TotalPoints AS r_totalpoints,
--                r.IO AS r_IO,
--                r.OffersAgency AS r_OffersAgency,
                r.Planid AS r_planid,
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
                COALESCE(adjr.adjvalueR,0) AS adjvaluer,
                COALESCE(adjp.adjvalueP,0) AS adjvaluep
            FROM
                oah_rates r
                INNER JOIN oah_limits l ON r.planid = l.planid
                LEFT OUTER JOIN (
                    SELECT
                        planid,
                        sum(adjvalue) adjvalueR
                    FROM oah_adjustments
                    WHERE
                        MINLOANAMT <= ? AND ? <= MAXLOANAMT
                        AND MINFICO<= ? AND MAXFICO >= ?
                        AND ? >= minltv AND ? <= maxltv
                        -- AND (proptype = ? OR proptype='')
                        AND (STATE=? or STATE = '')
                        AND AffectRateType='R'
                    GROUP BY planid
                )  adjr ON adjr.PlanID = r.planid
                LEFT OUTER JOIN (
                    SELECT
                        planid,
                        sum(adjvalue) adjvalueP
                    FROM oah_adjustments
                    WHERE
                        MINLOANAMT <= ? AND ? <= MAXLOANAMT
                        AND MINFICO<= ? AND MAXFICO >= ?
                        AND ? >= minltv AND ? <= maxltv
                        -- AND (proptype = ? OR proptype='')
                        AND (STATE=? or STATE = '')
                        AND AffectRateType='P'
                    GROUP BY planid
                )  adjp ON adjp.PlanID = r.planid

            WHERE 1=1
                -- Limits stuff
                AND (l.minltv <= ? AND l.maxltv >= ?)
                AND (l.minfico <= ? AND l.maxfico >= ?)
                AND (l.minloanamt <= ? AND l.maxloanamt >= ?)
                AND (r.stateid=? or r.stateid='')
                -- AND r.loanpurpose='PURCH'
                AND r.pmttype = ?
                AND r.loanterm = ?
                AND r.loantype = ?
                AND r.lock BETWEEN ? AND ?
                AND r.totalpoints = ?
                %s
            ORDER BY r_Institution, r_BaseRate
        """

        additional_query = ""
        if self.request['rate_structure'].upper() == 'ARM':
            additional_query = "AND r.io = 0 AND r.intadjterm = ? "
            qry_args.append(self.request['arm_type'][:self.request['arm_type'].index('/')])

        rows = execute_query(query % additional_query, qry_args, oursql.DictCursor)
        self.data = self._calculate_results(rows)

    def _calculate_results(self, data):
        """Remove extra rows. Return rates with numbers."""
        result = {}
        for row in data:
            row['final_points'] = row['adjvaluep'] + row['r_totalpoints']
            row['final_rates'] = "%.3f" % (row['adjvaluer'] + row['r_baserate'])
            if (
                row['r_planid'] not in result or
                abs(result[row['r_planid']]['r_totalpoints']) > abs(row['r_totalpoints']) or
                (abs(result[row['r_planid']]['r_totalpoints']) == abs(row['r_totalpoints']) and
                    result[row['r_planid']]['r_totalpoints'] < row['r_totalpoints']) or
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

    def _defaults(self):
        """Set defaults, calculate intermediate values for args."""
        self._set_ficos()
        self._set_loan_amount()
        tmp = dict((k, v[2]) for k, v in PARAMETERS.iteritems())
        tmp.update(self.request)
        self.request = tmp
        if self.request['rate_structure'].lower() == 'fixed':
            del self.request['arm_type']
        if 'fico' in self.request:
            del self.request['fico']

    def _set_loan_amount(self):
        """Set loan_amount, price and downpayment values."""
        if 'loan_amount' in self.request and 'price' in self.request and 'downpayment' in self.request:
            self.request['price'] = self.request['loan_amount'] + self.request['downpayment']
        elif 'loan_amount' in self.request and 'price' not in self.request and 'downpayment' not in self.request:
            self.request['price'] = self.request['loan_amount']
            self.request['downpayment'] = 0
        elif 'loan_amount' not in self.request and 'price' in self.request:
            if 'downpayment' not in self.request:
                self.request['downpayment'] = 0
            self.request['loan_amount'] = self.request['price'] - self.request['downpayment']
        else:
            self.request['loan_amount'] = PARAMETERS['loan_amount'][2]
            self.request['price'] = PARAMETERS['price'][2]
            self.request['downpayment'] = PARAMETERS['downpayment'][2]

    def _set_ficos(self):
        """Set minfico and maxfico values."""
        if 'minfico' not in self.request and 'maxfico' not in self.request and 'fico' in self.request:
            self.request['minfico'] = self.request['maxfico'] = self.request['fico']
        # only one of them is set
        elif 'minfico' in self.request and 'maxfico' not in self.request:
            self.request['maxfico'] = self.request['minfico']
        elif 'minfico' not in self.request and 'maxfico' in self.request:
            self.request['minfico'] = self.request['maxfico']
        elif 'minfico' in self.request and 'maxfico' in self.request and self.request['minfico'] > self.request['maxfico']:
            self.request['minfico'], self.request['maxfico'] = self.request['maxfico'], self.request['minfico']
