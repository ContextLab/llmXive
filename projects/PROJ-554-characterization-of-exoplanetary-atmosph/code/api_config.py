from typing import Dict, Any

QUERY_PARAMS: Dict[str, Any] = {
    "query": """
        SELECT 
          pl_name, 
          pl_contprov, 
          pl_orbper, 
          pl_orbsmax, 
          pl_bmassj, 
          pl_radj, 
          pl_eqt, 
          pl_insol, 
          st_met, 
          st_logg, 
          st_teff, 
          hostname, 
          hostname, 
          hostname, 
          hostname
        FROM exoplanet_archive
        WHERE 
          (pl_orbper < 10 OR pl_eqt > 1000)
          AND (pl_radj < 2.0 OR pl_bmassj < 0.1)
          AND pl_discmethod IN ('Transit', 'Radial Velocity')
    """,
    "format": "csv"
}
