import pandas as pd
import argparse
import json

mag_min = 14

# 2. Fonction de conversion pour l'Ascension Droite (RA: HH:MM:SS.SS -> Degrés)
def ra_to_degrees(ra_str):
    if pd.isna(ra_str) or not isinstance(ra_str, str):
        return None
    try:
        h, m, s = map(float, ra_str.split(':'))
        # 1 heure = 15 degrés
        return (h + m / 60.0 + s / 3600.0) * 15.0
    except:
        return None

# 3. Fonction de conversion pour la Déclinaison (Dec: +/-DD:MM:SS.SS -> Degrés)
def dec_to_degrees(dec_str):
    if pd.isna(dec_str) or not isinstance(dec_str, str):
        return None
    try:
        # Gestion du signe
        sign = -1.0 if dec_str.startswith('-') else 1.0
        if dec_str.startswith('+') or dec_str.startswith('-'):
            dec_str = dec_str[1:]
            
        d, m, s = map(float, dec_str.split(':'))
        return sign * (d + m / 60.0 + s / 3600.0)
    except:
        return None

def formatRA(ra):
    h,m,s = map(float,ra.split(':'))
    return f"{int(h):02d}h {int(m):02d}m {s}s"
    
def formatDec(dec):
    d,m,s = map(float,dec.split(':'))
    return f"{int(d):02d}° {int(m):02d}m {s}s"

    
def format_messier(val):
    if pd.isna(val) or val == '' or val == 'nan':
        return None
    
    # Au cas où il y a des zéros initiaux comme "031", on convertit en int puis en string
    # pour obtenir "M31" proprement
    try:
        num_clean = int(float(val))
        return f"M{num_clean}"
    except:
        return None
        
def convert_csv_to_panda(filename):
    df = pd.read_csv(filename, sep=';', dtype={'M': str})
    #we remove the useless columns
    df = df[['Name','Type','RA','Dec','Const','B-Mag','V-Mag','J-Mag','H-Mag','K-Mag','MajAx', 'MinAx', 'Hubble','M','NGC','IC','Cstar Names','Identifiers','Common names']]
    #we convert the ra and dec to degrees
    df['ra_deg'] = df['RA'].apply(ra_to_degrees)
    df['dec_deg'] = df['Dec'].apply(dec_to_degrees)
    #remove south hemisphere
    df = df[df['dec_deg'] > -40].copy()
    #we remove the useless object
    types_a_exclure = ['*', '**', 'NonEx', 'Dup']
    df = df[~df['Type'].isin(types_a_exclure)].copy()
    #convert col M 
    df['M'] = df['M'].apply(format_messier)
    #rename the col
    df = df.rename(columns={"Cstar Names": "Cstar_Names", "Common names": "Common_names", "B-Mag": "B_Mag", "V-Mag": "V_Mag", "J-Mag": "J_Mag", "H-Mag": "H_Mag", "K-Mag": "K_Mag", "MajAx": "Maj_Ax", "MinAx": "Min_Ax"})
    
    # colonne unique 'magnitude' qui prend V_Mag, et si c'est nul, prend B_Mag
    df['magnitude'] = df['V_Mag'].fillna(df['B_Mag'])
    #we remove the entries with low magnitude
    df =df[(df['magnitude'] < mag_min)]
    # round
    df['magnitude'] = df['magnitude'].round(2)
    #format RA
    df['RA'] = df['RA'].apply(formatRA)
    #format DEC
    df['Dec'] = df['Dec'].apply(formatDec)

    print(len(df.index))
    return df

def extract_hip_number(catalog_id):
    """Extract HIP number, ignoring A/B suffix: 'HIP 65378A' -> 65378"""
    if pd.isna(catalog_id):
        return None
    try:
        parts = catalog_id.split()
        if len(parts) >= 2:
            import re
            num_str = re.sub(r'[A-Za-z]', '', parts[1])
            return int(num_str)
        return None
    except:
        return None

def convert_dat_to_panda(filename):
    df = pd.read_csv(filename, sep=',', encoding='latin-1')
    #remove south hemisphere
    df = df[df['dec'] > -40].copy()

    #extract HIP number (ignoring A/B suffix)
    df['hip'] = df['catalog_id'].apply(extract_hip_number).astype('Int64')

    #keep only needed columns
    df = df[['hip','catalog_id','main_id','ra','dec','v_mag', 'common_name']]

    #clean the name as it contains NAME
    df['common_name'] = df['common_name'].replace('NAME ', '', regex=True)

    #deduplicate by HIP: keep the brightest star (lowest v_mag)
    df = df.sort_values('v_mag').drop_duplicates(subset='hip', keep='first')
    df = df.sort_values('hip').reset_index(drop=True)

    print(df.head())
    return df

def convert_constellations(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    result = []
    for const in data.get('constellations', []):
        # Extract short id: "CON modern Aql" -> "Aql"
        const_id = const['id'].split()[-1] if 'id' in const else None

        common_name = const.get('common_name', {})
        entry = {
            'id': const_id,
            'name': common_name.get('native'),
            'name_en': common_name.get('english'),
            'lines': const.get('lines', [])
        }
        result.append(entry)

    return result

def extract_dso_textures(filename):
    """Extract DSO name -> image URL mapping from Stellarium textures.json"""
    import re

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    result = {}

    for tile in data.get('subTiles', []):
        image_url = tile.get('imageUrl', '')
        if not image_url:
            continue

        # Remove file extension and suffixes like "-1", "-2", "-vasey"
        base_name = re.sub(r'(-\d+)?(-vasey)?\.png$', '', image_url.lower())

        # Patterns to match: m31, ngc224, ic434, barnard33, abell39, etc.
        patterns = [
            (r'^m(\d+)', 'M'),           # Messier: m31 -> M31
            (r'^ngc(\d+)', 'NGC'),       # NGC: ngc224 -> NGC224
            (r'^n(\d+)', 'NGC'),       # NGC: ngc224 -> NGC224
            (r'^ic(\d+)', 'IC'),         # IC: ic434 -> IC434
            (r'^barnard(\d+)', 'B'),     # Barnard: barnard33 -> B33
            (r'^abell(\d+)', 'Abell'),   # Abell: abell39 -> Abell39
            (r'^sh2[_-]?(\d+)', 'Sh2-'), # Sharpless: sh2_101 -> Sh2-101
            (r'^ldn(\d+)', 'LDN'),       # Lynds Dark: ldn1622 -> LDN1622
            (r'^lbn(\d+)', 'LBN'),       # Lynds Bright: lbn782 -> LBN782
            (r'^ced(\d+)', 'Ced'),       # Cederblad: ced211 -> Ced211
            (r'^vdb(\d+)', 'VdB'),       # Van den Bergh: vdb142 -> VdB142
            (r'^rcw(\d+)', 'RCW'),       # RCW: rcw49 -> RCW49
            (r'^mel(\d+)', 'Mel'),       # Melotte: mel15 -> Mel15
            (r'^cr(\d+)', 'Cr'),         # Collinder: cr399 -> Cr399
            (r'^tr(\d+)', 'Tr'),         # Trumpler: tr37 -> Tr37
            (r'^ugc(\d+)', 'UGC'),       # UGC: ugc1810 -> UGC1810
            (r'^pgc(\d+)', 'PGC'),       # PGC: pgc2557 -> PGC2557
            (r'^dwb(\d+)', 'DWB'),       # DWB: dwb111 -> DWB111
        ]

        dso_name = None
        for pattern, prefix in patterns:
            match = re.match(pattern, base_name)
            if match:
                dso_name = f"{prefix}{match.group(1)}"
                break

        if dso_name:
            # Keep first image if multiple exist for same object
            if dso_name not in result:
                result[dso_name] = image_url

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ngc", help="NGC Objects", type=str)
    parser.add_argument("--stars", help="HD Stars", type=str)
    parser.add_argument("--constellations", help="Constellations", type=str)
    parser.add_argument("--textures", help="Stellarium textures.json", type=str)
    args = parser.parse_args()

    if args.ngc:
        df = convert_csv_to_panda(args.ngc)
        df.to_json("data/ngc.json", orient="records", indent=4)
    elif args.stars:
        df = convert_dat_to_panda(args.stars)
        df.to_json("data/stars.json", orient="records", indent=4)
    elif args.constellations:
        constellations = convert_constellations(args.constellations)
        with open("data/constellations_lines.json", 'w', encoding='utf-8') as f:
            json.dump(constellations, f, indent=4, ensure_ascii=False)
    elif args.textures:
        textures = extract_dso_textures(args.textures)
        with open("data/dso_images.json", 'w', encoding='utf-8') as f:
            json.dump(textures, f, indent=4, ensure_ascii=False)
        print(f"Extracted {len(textures)} DSO image mappings")
    