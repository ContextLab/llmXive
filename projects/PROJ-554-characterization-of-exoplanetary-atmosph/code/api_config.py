"""
Configuration for NASA Exoplanet Archive API queries.

Defines query parameters for filtering Hot Jupiters and Super-Earths.
"""

from typing import Dict, Any

# NASA Exoplanet Archive TAP API base URL
# Using the standard async TAP endpoint for bulk data retrieval
API_BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/async"

# Query parameters for fetching hot Jupiters and super-Earths
# This dictionary is consumed by code/download.py to construct the API request.
# The ADQL query specifically filters for:
# 1. Discovery method: Transit
# 2. Planet type: 'Hot Jupiter' OR 'Super Earth' (case-insensitive in archive, but explicit here)
# 3. Transit flag confirmed (1)
# 4. Non-null equilibrium temperature and stellar metallicity (required for downstream analysis)
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
            pl_type,
            pl_bmiss,
            pl_radjerr,
            pl_massjerr,
            pl_eqterr,
            st_meterr,
            inst_name,
            wavelength
        FROM pscomp
        WHERE pl_discmethod = 'Transit' 
        AND (pl_type = 'Hot Jupiter' OR pl_type = 'Super Earth')
        AND tran_flag = 1
        AND pl_eqt IS NOT NULL
        AND st_met IS NOT NULL
        AND spec_res IS NOT NULL
    """
}

# SNR threshold for determining censored data in downstream analysis (T019)
# Values below this threshold are treated as upper limits.
SNR_THRESHOLD = 5.0

# Minimum spectral resolution for valid data inclusion
# Used to filter out low-resolution observations that cannot resolve water features.
MIN_SPECTRAL_RESOLUTION = 100

# Additional metadata for logging and identification
QUERY_DESCRIPTION = "Hot Jupiter and Super-Earth Transmission Spectra Metadata"
DATA_SOURCE = "NASA Exoplanet Archive (TAP)"