"""
Query SIMBAD for stars by magnitude filter.
Uses direct TAP queries with CSV format to avoid Python 3.14 + Windows overflow bug.
"""
import pathlib
import requests
from io import StringIO
from astropy.table import Table
import tqdm


def query_catalog_by_magnitude(
    catalog: str,  # 'HIP', 'SAO', 'HD', 'HR'
    max_v_mag: float = 6.5,
    output_path: pathlib.Path = None,
) -> Table:
    """
    Query SIMBAD for all stars in a catalog brighter than max_v_mag.

    Args:
        catalog: Catalog prefix ('HIP', 'SAO', 'HD', 'HR')
        max_v_mag: Maximum V magnitude (brighter = smaller number)
        output_path: Optional path to save results

    Returns:
        Astropy Table with results
    """
    url = 'https://simbad.cds.unistra.fr/simbad/sim-tap/sync'

    # Query all stars in catalog with V magnitude filter
    # LEFT JOIN to get common/historical name (prefixed with 'NAME ' in SIMBAD)
    query = f"""
    SELECT
        ident.id AS catalog_id,
        main_id, ra, dec, pmra, pmdec,
        plx_value, plx_err, otype, sp_type,
        rvz_radvel, rvz_err,
        flux.flux AS V_mag,
        name_ident.id AS common_name
    FROM basic
    JOIN ident ON ident.oidref = basic.oid
    JOIN flux ON flux.oidref = basic.oid
    LEFT JOIN ident AS name_ident ON name_ident.oidref = basic.oid
                                  AND name_ident.id LIKE 'NAME %'
    WHERE ident.id LIKE '{catalog} %'
      AND flux.filter = 'V'
      AND flux.flux <= {max_v_mag}
    """

    print(f"Querying {catalog} stars with V <= {max_v_mag}...")

    response = requests.post(url, data={
        'REQUEST': 'doQuery',
        'LANG': 'ADQL',
        'FORMAT': 'csv',
        'QUERY': query
    }, timeout=600)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text[:500])
        return Table()

    # Parse CSV to astropy Table
    import pandas as pd
    df = pd.read_csv(StringIO(response.text))
    table = Table.from_pandas(df)
    print(f"Found {len(table)} {catalog} stars with V <= {max_v_mag}")

    if output_path and len(table) > 0:
        #table.write(output_path, format='ascii', overwrite=True)
        table.write(output_path, format='csv', overwrite=True)
        print(f"Saved to {output_path}")

    return table


def query_all_catalogs_by_magnitude(max_v_mag: float = 6.5):
    """Query all catalogs (HIP, SAO, HD, HR) by magnitude."""
    output_dir = pathlib.Path("simbad_query_results") / f"v_mag_{max_v_mag}"
    output_dir.mkdir(parents=True, exist_ok=True)

    catalogs = ['HIP', 'SAO', 'HD', 'HR']

    for catalog in tqdm.tqdm(catalogs, desc="Querying catalogs"):
        output_path = output_dir / f"{catalog.lower()}_v{max_v_mag}.csv"
        if output_path.exists():
            print(f"Skipping {catalog} - already exists")
            continue
        query_catalog_by_magnitude(catalog, max_v_mag, output_path)

    print(f"\nResults saved to {output_dir}/")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Query SIMBAD catalogs by magnitude")
    parser.add_argument("--mag", type=float, default=6.5,
                        help="Maximum V magnitude (default: 6.5, naked eye limit)")
    parser.add_argument("--catalog", type=str, default=None,
                        help="Single catalog to query (HIP, SAO, HD, HR). If not set, queries all.")
    args = parser.parse_args()

    if args.catalog:
        output_dir = pathlib.Path("simbad_query_results") / f"v_mag_{args.mag}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.catalog.lower()}_v{args.mag}.csv"
        query_catalog_by_magnitude(args.catalog.upper(), args.mag, output_path)
    else:
        query_all_catalogs_by_magnitude(args.mag)