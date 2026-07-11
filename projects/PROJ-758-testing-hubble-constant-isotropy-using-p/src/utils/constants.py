"""
Physical constants and Pantheon+ dataset metadata.

This module provides standard physical constants used in cosmological
calculations and metadata regarding the Pantheon+ supernova dataset.
"""

from typing import Final, Dict, Any

# Physical Constants (CODATA 2018 / Standard Cosmology values)
# Speed of light in km/s
C_KM_S: Final[float] = 299_792.458

# Reference Hubble Constant values (km/s/Mpc) for comparison
# Planck 2018 (TT,TE,EE+lowE+lensing)
H0_PLANCK_2018: Final[float] = 67.4
H0_PLANCK_2018_ERR: Final[float] = 0.5

# SH0ES 2022 (Cepheid-calibrated)
H0_SH0ES_2022: Final[float] = 73.04
H0_SH0ES_2022_ERR: Final[float] = 1.04

# Pantheon+ Dataset Metadata
# Source: Scolnic et al. (2022), Pantheon+ Analysis
PANETHEON_PLUS_METADATA: Final[Dict[str, Any]] = {
    "name": "Pantheon+",
    "description": "Pantheon+ sample of Type Ia Supernovae",
    "reference": "Scolnic et al. (2022), arXiv:2112.03863",
    "zenodo_record_id": "10.5281/zenodo.1002345",
    "zenodo_doi": "10.5281/zenodo.1002345",
    "data_version": "v1.0",
    "n_supernovae": 1701,
    "redshift_range": {
        "min": 0.001,
        "max": 2.26
    },
    "default_redshift_cut": 0.15,
    "coordinates": {
        "system": "ICRS",
        "units": "degrees",
        "columns": ["ra", "dec"]
    },
    "distance_modulus_column": "mu",
    "distance_modulus_error_column": "mu_err",
    "peculiar_velocity_correction": {
        "model": "CosmicFlows-3",
        "implementation": "pecvel"
    }
}

# Analysis Configuration Defaults
ANALYSIS_CONFIG: Final[Dict[str, Any]] = {
    "healpix_nside": 4,
    "healpix_ordering": "NESTED",
    "min_snr": 0.0,  # Quality flag threshold
    "max_redshift_local": 0.15,
    "min_sns_per_pixel": 30,
    "random_seed": 42
}