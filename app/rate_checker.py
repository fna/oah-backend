import psycopg2
import psycopg2.extras
import os

from utils import PARAMETERS, STATE_ABBR


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
        self._parse_args(request)
        if request.path == '/rate-checker':
            #self.loanterm, _, self.pmttype = self.request['loan_type'].split(' ')
            self._get_data()
        elif request.path == '/county-limit':
            self._get_county_limit()
        return self._output()

    def _output(self):
        """Compile response"""
        return {
            "status": self.status,
            "request": self.request,
            "data": self.data,
            "errors": self.errors,
        }

    def _get_county_limit(self):
        """Get FHA and GSE county limits."""
        query = """
            SELECT
                gse_limit, fha_limit
            FROM
                county_limits cl
                INNER JOIN state s ON s.state_id = cl.state_id
                INNER JOIN county c ON c.county_id = cl.county_id
            WHERE
                county_name = %s
                AND state_name = %s
        """
        try:
            dbname = os.environ.get('OAH_DB_NAME', 'oah')
            dbhost = os.environ.get('OAH_DB_HOST', 'localhost')
            dbuser = os.environ.get('OAH_DB_USER', 'user')
            dbpass = os.environ.get('OAH_DB_PASS', 'password')
            conn = psycopg2.connect('dbname=%s host=%s user=%s password=%s' % (dbname, dbhost, dbuser, dbpass))
            cur = conn.cursor()
            cur.execute(query, (self.request['county'], self.request['state']))
            data = cur.fetchone()
            self.data.append({'gse_limit': str(data[0]), 'fha_limit': str(data[1])})
            cur.close()
            conn.close()
        except Exception as e:
            return "Exception %s" % e

    def _get_data(self):
        """Calculate results."""
        data = []
        minltv = maxltv = float(self.request['loan_amount']) / self.request['price'] * 100

        qry_args = [self.request['loan_amount'], self.request['loan_amount'], self.request['minfico'],
                    self.request['maxfico'], minltv, maxltv, self.request['state'], self.request['loan_amount'],
                    self.request['loan_amount'], self.request['minfico'], self.request['maxfico'], minltv, maxltv,
                    self.request['state'], minltv, maxltv, self.request['minfico'], self.request['maxfico'],
                    self.request['loan_amount'], self.request['loan_amount'], self.request['state'],
                    self.request['rate_structure'].upper(), self.request['loan_term'], self.request['loan_type']]

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
                AND r.loanterm=%s
                AND r.loantype=%s

            ORDER BY r_Institution, r_BaseRate
        """
        try:
            dbname = os.environ.get('OAH_DB_NAME', 'oah')
            dbhost = os.environ.get('OAH_DB_HOST', 'localhost')
            dbuser = os.environ.get('OAH_DB_USER', 'user')
            dbpass = os.environ.get('OAH_DB_PASS', 'password')
            conn = psycopg2.connect('dbname=%s host=%s user=%s password=%s' % (dbname, dbhost, dbuser, dbpass))
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query, qry_args)
            self.data = self._calculate_results(cur.fetchall())
            cur.close()
            conn.close()
        except Exception as e:
            print "Exception: %s" % e
            return "Exception %s" % e

    def _calculate_results(self, data):
        """Remove extra rows. Return rates with numbers."""
        result = {}
        for row in data:
            row['final_points'] = row['adjvaluep'] + row['r_totalpoints']
            row['final_rates'] = "%.3f" % (row['adjvaluer'] + row['r_baserate'])
            if (
                row['r_planid'] not in result or
                abs(result[row['r_planid']]['r_totalpoints']) > abs(row['r_totalpoints']) or
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

    def _parse_args(self, request):
        """Parse API arguments"""
        # get initial values and check types
        args = request.args
        path = request.path[1:]
        #TODO : remove params = {param: self._check_type(path, param, args.get(param, None)) for param in PARAMETERS[path].keys()}
        params = {}
        for param in PARAMETERS[path].keys():
            params[param] = self._check_type(path, param, args.get(param, None))
        if path == 'rate-checker':
            self._set_ficos(params)
            self._set_loan_amount(params, PARAMETERS[path])
        # set defaults for None values
        for param in params.keys():
            if params.get(param) is None:
                params[param] = PARAMETERS[path][param][2]
        # calculate loan_amt
        if path == 'rate-checker':
            params['loan_amount'] = params['price'] - params['downpayment']
        #TODO remove self.request = {param: params[param] for param in params if params[param] is not None}
        self.request = {}
        for param in params:
            if params[param] is not None:
                self.request[param] = params[param]

    def _check_type(self, path, param, value):
        """Check type of the value."""
        if value is None:
            return None
        try:
            return PARAMETERS[path][param][0](value)
        except:
            self.errors.append(PARAMETERS[path][param][1] % value)
            self.status = "Error"
            return None

    def _set_loan_amount(self, args, params):
        """Set loan_amount, price and downpayment values."""
        if args['loan_amount'] is not None and args['price'] is not None and args['downpayment'] is not None:
            args['price'] = args['loan_amount'] + args['downpayment']
        elif args['loan_amount'] and not args['price'] and not args['downpayment']:
            args['price'] = args['loan_amount']
            args['downpayment'] = 0
        elif not args['loan_amount'] and args['price']:
            if not args['downpayment']:
                args['downpayment'] = 0
            args['loan_amount'] = args['price'] - args['downpayment']
        else:
            args['loan_amount'] = params['loan_amount'][2]
            args['price'] = params['price'][2]
            args['downpayment'] = params['downpayment'][2]

    def _set_ficos(self, args):
        """Set minfico and maxfico values."""
        if not args['minfico'] and not args['maxfico'] and args['fico']:
            args['minfico'] = args['maxfico'] = args['fico']
        # only one of them is set
        elif bool(args['minfico']) != bool(args['maxfico']):
            args['maxfico'] = args['minfico'] = args['maxfico'] if args['maxfico'] else args['minfico']
        elif args['minfico'] and args['maxfico'] and args['minfico'] > args['maxfico']:
            args['minfico'], args['maxfico'] = args['maxfico'], args['minfico']
        del args['fico']
