import oursql

from utils import (
    parse_args, execute_query, is_float, is_str, is_arm,
    is_int, is_state_abbr)

PARAMETERS = {
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
        '5/1',
    ],
    'loan_term': [
        is_int,
        'Loan term must be a numeric value, |%s| provided',
        30,
    ],
    'price': [
        is_float,
        'House price must be a numeric value, |%s| provided',
        200000,
    ],
    'loan_amount': [
        is_float,
        'Loan amount must be a numeric value, |%s| provided',
        180000,
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
        700
    ],
    'maxfico': [
        is_int,
        'MaxFICO must be an integer, |%s| provided',
        719
    ],
    'points': [
        is_float,
        'Points value must be a numeric, |%s| provided',
        0
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
    """ This is the class that powers the rate checker. It embodies
    all the business and querying logic for the rate checker. """

    def __init__(self):
        """Set parameters to default values."""
        self.errors = []
        self.data = []
        self.status = "OK"
        self.request = {}

    def process_request(self, request):
        """The main function which processes request and returns result
        back."""

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

        ltv = float(self.request['loan_amount']) / self.request['price'] * 100
        minltv = maxltv = ltv

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

        qry_args = [
            self.request['loan_amount'], self.request['loan_amount'],
            self.request['minfico'], self.request['maxfico'], minltv, maxltv,
            self.request['state'], self.request['loan_amount'],
            self.request['loan_amount'], self.request['minfico'],
            self.request['maxfico'], minltv, maxltv, self.request['state'],
            minltv, maxltv, self.request['minfico'], self.request['maxfico'],
            self.request['loan_amount'], self.request['loan_amount'],
            self.request['state'], self.request['rate_structure'].upper(),
            self.request['loan_term'], self.request['loan_type'].upper(),
            minlock, maxlock]

        query = """
            SELECT
                r.Institution AS r_institution,
                r.Lock AS r_lock,
                r.BaseRate AS r_baserate,
                r.TotalPoints AS r_totalpoints,
                r.Planid AS r_planid,
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
                    WHERE 1=1
                        AND (
                            (MINLOANAMT <= ? AND MAXLOANAMT >= ? AND MINLOANAMT <> 0 AND MAXLOANAMT <> 999999999)
                            OR (MINFICO <= ? AND MAXFICO >= ? AND (MINFICO > 0 OR (MINFICO <> 0 AND MAXFICO <> 999)) AND MINLTV <= ? AND MAXLTV >= ?)
                            OR (STATE=?)
                        )
                        AND AffectRateType='R'
                    GROUP BY planid
                )  adjr ON adjr.PlanID = r.planid
                LEFT OUTER JOIN (
                    SELECT
                        planid,
                        sum(adjvalue) adjvalueP
                    FROM oah_adjustments
                    WHERE 1=1
                        AND (
                            (MINLOANAMT <= ? AND MAXLOANAMT >= ? AND MINLOANAMT <> 0 AND MAXLOANAMT <> 999999999)
                            OR (MINFICO <= ? AND MAXFICO >= ? AND (MINFICO > 0 OR (MINFICO <> 0 AND MAXFICO <> 999)) AND MINLTV <= ? AND MAXLTV >= ?)
                            OR (STATE=?)
                        )

                        AND AffectRateType='P'
                    GROUP BY planid
                )  adjp ON adjp.PlanID = r.planid

            WHERE 1=1
                -- Limits stuff
                AND (l.minltv <= ? AND l.maxltv >= ?)
                AND (l.minfico <= ? AND l.maxfico >= ?)
                AND (l.minloanamt <= ? AND l.maxloanamt >= ?)
                AND (r.stateid=?)
                AND r.loanpurpose='PURCH'
                AND r.pmttype = ?
                AND r.loanterm = ?
                AND r.loantype = ?
                AND r.lock BETWEEN ? AND ?
                %s
            ORDER BY r_Institution, r_BaseRate
        """

        additional_query = ""
        if self.request['rate_structure'].upper() == 'ARM':
            additional_query = "AND r.io = 0 AND r.intadjterm = ? "
            qry_args.append(
                self.request['arm_type'][:self.request['arm_type'].index('/')])

        rows = execute_query(
            query % additional_query, qry_args, oursql.DictCursor)

        self.data = self._calculate_results(rows)

    def bucket_results(self, result):
        """ This API allows users to draw a histogram at the end, so we bucket
        the results here. """

        buckets = {}
        for row in result:
            if result[row]['final_rates'] in buckets:
                buckets[result[row]['final_rates']] += 1
            else:
                buckets[result[row]['final_rates']] = 1
        return buckets

    def closer_to_zero(self, original_final_points, new_final_points):
        """ For each plan, we pick the results with the final points that are
        closest to zero. """

        if abs(new_final_points) < abs(original_final_points):
            return True
        elif abs(new_final_points) == abs(original_final_points):
            return new_final_points > 0 and original_final_points < 0
        return False

    def _calculate_results(self, data):
        """ Further apply filters to the results, based on calculations made
        during the SQL query. """

        maxpoints = self.request['points'] + 0.5
        minpoints = self.request['points'] - 0.5

        filtered_on_points = []

        for row in data:
            row['final_points'] = row['adjvaluep'] + row['r_totalpoints']
            final_points = row['final_points']
            if final_points <= maxpoints and final_points >= minpoints:
                row['final_rates'] = "%.3f" % (
                    row['adjvaluer'] + row['r_baserate'])
                filtered_on_points.append(row)

        result = {}
        for row in filtered_on_points:
            if row['r_planid'] not in result:
                result[row['r_planid']] = row
            elif self.closer_to_zero(
                result[row['r_planid']]['final_points'], row['final_points']):
                    result[row['r_planid']] = row

        return self.bucket_results(result)

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
        """ Set loan_amount and price values. If one is not provided, determine
        using the other. """

        req = self.request
        amount = 'loan_amount'

        if amount in req and 'price' not in req:
            req['price'] = int(req[amount] * 1.1)
        elif amount not in req and 'price' in req:
            req[amount] = int(req['price'] * 0.9)
        elif amount in req and 'price' in req and req[amount] > req['price']:
            req[amount], req['price'] = req['price'], req[amount]

    def _set_ficos(self):
        """ Set the min and max FICO scores """
        req = self.request

        if 'minfico' not in req and 'maxfico' not in req and 'fico' in req:
            req['minfico'] = req['fico']
            req['maxfico'] = req['fico']

        # Only one of them is set
        elif 'minfico' in req and 'maxfico' not in req:
            req['maxfico'] = req['minfico']
        elif 'minfico' not in req and 'maxfico' in req:
            req['minfico'] = req['maxfico']
        elif ('minfico' in req and 'maxfico' in req and
                req['minfico'] > req['maxfico']):
                req['minfico'], req['maxfico'] = req['maxfico'], req['minfico']

        # so that results for minfico=700,maxfico=720 and
        # minfico=720,maxfico=740 don't overlap

        if ('maxfico' in req and 'minfico' in req and
            req['maxfico'] != req['minfico']):
                self.request['maxfico'] -= 1
