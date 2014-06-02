from utils import parse_args, execute_query, is_state_fips, is_state_abbr

PARAMETERS = {
    'state': [
        is_state_abbr,
        'Value provided, |%s|, doesn\'t look like a state abbreviation',
        'DC'
    ],
    'state_fips': [
        is_state_fips,
        'State fips must be a two-digit string, |%s| provided',
        '11',
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
        self._county_limit_data()
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
        qry_args = self.request.values() * 2
        query = """
            SELECT
                state_name, county_name, cl.complete_fips,
                gse_limit, fha_limit, va_limit
            FROM
                oah_county_limits cl
                INNER JOIN oah_county c ON c.complete_fips = cl.complete_fips
                INNER JOIN oah_state s ON SUBSTR(c.complete_fips, 1, 2) = s.state_fips
            WHERE
                s.state_fips = ? OR s.state_abbr = ?
        """
        rows = execute_query(query, qry_args)
        for row in rows:
            state, county, fips, gse, fha, va = row
            self.data.append({
                'state': state,
                'county': county,
                'complete_fips': fips,
                'gse_limit': str(gse),
                'fha_limit': str(fha),
                'va_limit': str(va),
            })

    def _defaults(self):
        """Set default values."""
        if not self.request:
            self.request['state_fips'] = PARAMETERS['state_fips'][2]
