from utils import parse_args, execute_query, is_state_name, is_str

PARAMETERS = {
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
        results = parse_args(request, PARAMETERS)
        self.request = results['results']
        if len(results['errors']) > 0:
            self.errors = results['errors']
            self.status = 'Error'
        self._defaults()
        self._data()
        return self._output()

    def _output(self):
        """Compile response."""
        return {
            "status": self.status,
            "request": self.request,
            "data": self.data,
            "errors": self.errors,
        }

    def _data(self):
        """Get FHA and GSE county limits."""
        qry_args = self.request.values()
        query = """
            SELECT
                gse_limit, fha_limit
            FROM
                oah_county_limits cl
                INNER JOIN oah_state s ON s.stateid = cl.stateid
                INNER JOIN oah_county c ON c.countyid = cl.countyid
            WHERE
                county_name = ?
                AND state_name = ?
        """
        rows = execute_query(query, qry_args)
        if rows and rows[0]:
            self.data = [{'gse_limit': str(rows[0][0]), 'fha_limit': str(rows[0][1])}]

    def _defaults(self):
        """Set default values."""
        # doesn't really make sense here
        tmp = dict((k, v[2]) for k, v in PARAMETERS.iteritems())
        tmp.update(self.request)
        self.request = tmp
