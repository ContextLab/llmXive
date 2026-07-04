"""
Configuration for NASA Exoplanet Archive API queries.

Defines query parameters for filtering Hot Jupiters and Super-Earths.
"""

from typing import Dict, Any

# NASA Exoplanet Archive TAP API base URL
API_BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/async"

# Query parameters for fetching hot Jupiters and super-Earths
QUERY_PARAMS: Dict[str, Any] = {
    "REQUEST": "doQuery",
    "LANG": "ADQL",
    "FORMAT": "csv",
    "QUERY": """
        SELECT 
            pl_name, 
            pl_orbper, 
            pl_radj, 
            pl_massj, 
            pl_eqt, 
            st_met, 
            st_dist, 
            tran_flag, 
            ra, 
            dec, 
            pmra, 
            pmdec, 
            e_pmra, 
            e_pmdec, 
            hst_snr, 
            jwst_snr, 
            spec_res,
            pl_type
        FROM pscomp
        WHERE pl_discmethod = 'Transit' 
        AND (pl_type = 'Hot Jupiter' OR pl_type = 'Super Earth')
        AND tran_flag = 1
        AND pl_eqt IS NOT NULL
        AND st_met IS NOT NULL
    """
}

# SNR threshold for determining censored data
SNR_THRESHOLD = 5.0

# Minimum spectral resolution for valid data
MIN_SPECTRAL_RESOLUTION = 100
