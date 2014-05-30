from utils import parse_args, execute_query, is_state_name, is_str, is_fips, is_state_fips

PARAMETERS = {
    '/county-limit/list': {
        'state': [
            is_state_name,
            'State must be a string, |%s| provided',
            'DISTRICT OF COLUMBIA'
        ],
        'state_fips': [
            is_state_fips,
            'State fips must be a two-digit string, |%s| provided',
            '11'
        ],
    },
    '/county-limit': {
        'complete_fips': [
            is_fips,
            'Complete fips must be a five-digit string, |%s| provided',
            '11001',
        ]
    }
}


class CountyLimit(object):
    """To have everything consistent."""

    def __init__(self):
        """Set defaults."""
        self.errors = []
        self.data = []
        self.status = "OK"
        self.request = {}

    def process_request(self, request):
        """Get input, return results."""
        results = parse_args(request, PARAMETERS[request.path])
        self.request = results['results']
        if len(results['errors']) > 0:
            self.errors = results['errors']
            self.status = 'Error'
        if request.path == '/county-limit':
            self._defaults('/county-limit')
            self._county_limit_data()
        elif request.path == '/county-limit/list':
            self._county_limit_list()
        return self._output()

    def _output(self):
        """Compile response."""
        return {
            "status": self.status,
            "request": self.request,
            "data": self.data,
            "errors": self.errors,
        }

    def _county_limit_data(self):
        """Get FHA and GSE county limits."""
        qry_args = self.request.values()
        query = """
            SELECT
                state_name, county_name,
                gse_limit, fha_limit, va_limit
            FROM
                oah_county_limits cl
                INNER JOIN oah_county c ON c.complete_fips = cl.complete_fips
                INNER JOIN oah_state s ON SUBSTR(c.complete_fips, 1, 2) = s.state_fips
            WHERE
                cl.complete_fips = ?
        """
        rows = execute_query(query, qry_args)
        if rows and rows[0]:
            state, county, gse, fha, va = rows[0]
            self.data = [{
                'state': state,
                'county': county,
                'gse_limit': str(gse),
                'fha_limit': str(fha),
                'va_limit': str(va),
            }]

    def _county_limit_list(self):
        """Return list of counties in a state."""
        qry_args = self.request.values()
        query = """
            SELECT
                state_name, state_fips, c.*
            FROM
                oah_county c
                INNER JOIN oah_state s ON SUBSTR(complete_fips, 1, 2) = state_fips
            WHERE
                1 = 1
        """
        if qry_args:
            query += " AND state_name = ? OR state_fips = ? "
            qry_args = [qry_args[0], qry_args[0]]
        rows = execute_query(query, qry_args)
        data = {}
        for row in rows:
            if row[0] not in data:
                data[row[0]] = {
                    'state_fips': row[1],
                    'counties': [{
                        'county_name': row[2],
                        'county_fips': row[3],
                        'complete_fips': row[4],
                    }],
                }
            else:
                data[row[0]]['counties'].append({
                    'county_name': row[2],
                    'county_fips': row[3],
                    'complete_fips': row[4],
                })
        self.data.append(data)

    def _defaults(self, path):
        """Set default values."""
        tmp = dict((k, v[2]) for k, v in PARAMETERS[path].iteritems())
        tmp.update(self.request)
        self.request = tmp
