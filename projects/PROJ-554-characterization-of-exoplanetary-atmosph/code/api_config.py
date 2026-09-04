from typing import Dict, Any

# Configuration for NASA Exoplanet Archive API queries
# Targeting Hot Jupiters and Super-Earths
QUERY_PARAMS: Dict[str, Any] = {
    'cmd': 'select * from pscomp', # Select from the comprehensive planet table
    'table': 'pscomp',
    'cols': 'pl_name,pl_orbper,pl_radj,pl_eqt,pl_masse,st_met,snr,pl_tranflag,pl_massj,pl_radj',
    'limit': 10000,
    'format': 'json'
}
