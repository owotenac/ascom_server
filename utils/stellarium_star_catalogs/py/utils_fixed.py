"""
Fixed SIMBAD query utilities using direct TAP queries.
Workaround for Python 3.14 + Windows overflow bug in astroquery.
"""
from pyvo import dal
from astropy.table import Table, vstack
import warnings


class FixedSimbad:
    """Direct TAP-based SIMBAD querier that avoids the object_number_id overflow bug."""

    TIMEOUT = 99999
    TAP_URL = 'https://simbad.cds.unistra.fr/simbad/sim-tap'

    # Columns to query (matching the original utils.py fields)
    COLUMNS = [
        'main_id',
        'ra',
        'dec',
        'pmra',
        'pmdec',
        'plx_value',
        'plx_err',
        'otype',
        'sp_type',
        'rvz_radvel',
        'rvz_err',
    ]

    # Additional columns that require joins (handled separately)
    # ids, U, B, V, R, I, G, J, H, K - photometry needs flux table join

    def __init__(self):
        self.tap = dal.TAPService(self.TAP_URL)

    def query_objects(self, object_ids: list) -> Table:
        """
        Query SIMBAD for a list of object IDs (e.g., ['HIP 1', 'HIP 2']).
        Returns an astropy Table with results.
        """
        if not object_ids:
            return Table()

        # Escape single quotes in IDs
        escaped_ids = [id_.replace("'", "''") for id_ in object_ids]
        id_list = ", ".join(f"'{id_}'" for id_ in escaped_ids)

        columns_str = ", ".join(self.COLUMNS)

        query = f"""
        SELECT {columns_str}, ident.id as input_id
        FROM basic
        JOIN ident ON ident.oidref = basic.oid
        WHERE ident.id IN ({id_list})
        """

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                job = self.tap.run_sync(query, maxrec=len(object_ids) * 2)
                return job.to_table()
        except Exception as e:
            print(f"Query failed: {e}")
            return Table()


# Create a compatible instance
custom_simbad = FixedSimbad()