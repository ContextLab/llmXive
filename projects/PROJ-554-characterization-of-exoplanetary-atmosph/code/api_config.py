"""
API configuration for NASA Exoplanet Archive queries.
"""

from typing import Dict, Any

# Query parameters for Hot Jupiters and Super-Earths
# Filters for planets with transmission spectra data
QUERY_PARAMS: Dict[str, Any] = {
    "QUERY": (
        "SELECT "
        "pl_name, pl_hostname, pl_orbper, pl_radj, pl_massj, "
        "pl_eqt, pl_orbper, pl_solrad, pl_orbincl, "
        "st_teff, st_met, st_logg, "
        "hostname, "
        "tran_flag, "
        "dispersion, "
        "wlen_min, wlen_max, "
        "SNR, "
        "Resolution "
        "FROM exoplanet_archive "
        "WHERE pl_discmethod LIKE '%Transit%' "
        "AND pl_radj > 0.8 "
        "AND pl_orbper < 10 "
        "AND tran_flag = 1 "
        "AND pl_eqt IS NOT NULL "
        "AND st_met IS NOT NULL "
    )
}

# Alternative query for broader selection if needed
QUERY_PARAMS_BROAD: Dict[str, Any] = {
    "QUERY": (
        "SELECT "
        "pl_name, pl_hostname, pl_orbper, pl_radj, pl_massj, "
        "pl_eqt, pl_orbper, pl_solrad, pl_orbincl, "
        "st_teff, st_met, st_logg, "
        "hostname, "
        "tran_flag, "
        "dispersion, "
        "wlen_min, wlen_max, "
        "SNR, "
        "Resolution "
        "FROM exoplanet_archive "
        "WHERE pl_discmethod LIKE '%Transit%' "
        "AND pl_eqt IS NOT NULL "
        "AND st_met IS NOT NULL "
        "AND tran_flag = 1 "
    )
}
