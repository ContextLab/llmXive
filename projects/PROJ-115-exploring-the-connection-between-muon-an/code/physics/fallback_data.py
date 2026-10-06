"""
Fallback data sources for physics constants and experimental limits.
Used when real-time data fetching fails or for reproducibility.
"""
import numpy as np
from typing import Dict, Tuple, List

# Planck 2018 results (from Planck Collaboration VI 2020)
# Omega_m h^2 = 0.1430 +/- 0.0011
# H0 = 67.36 +/- 0.54 km/s/Mpc
PLANCK_2018_CONSTANTS = {
    "Omega_m_h2": 0.1430,
    "Omega_m_h2_uncertainty": 0.0011,
    "H0": 67.36,
    "H0_uncertainty": 0.54,
    "Omega_b_h2": 0.02237,
    "sigma_8": 0.8111,
    "source": "Planck 2018 Final Results (Planck Collaboration VI, 2020)",
    "doi": "10.1051/0004-6361/201833910"
}

# Xenon1T 2018 Spin-Independent Cross-Section Limits
# Approximated from Fig. 2 of "Dark Matter Search Results from a One Ton-Year Exposure of XENON1T"
# Values represent the exclusion curve (m_DM [GeV] vs sigma_SI [cm^2])
XENON1T_LIMITS = [
    (10.0, 1.1e-45),
    (20.0, 3.5e-46),
    (30.0, 1.5e-46),
    (40.0, 8.0e-47),
    (50.0, 5.0e-47),
    (60.0, 3.5e-47),
    (70.0, 2.5e-47),
    (80.0, 2.0e-47),
    (90.0, 1.6e-47),
    (100.0, 1.4e-47),
    (200.0, 8.0e-48),
    (500.0, 4.5e-48),
    (1000.0, 3.0e-48),
    (2000.0, 2.5e-48),
    (5000.0, 2.2e-48),
    (10000.0, 2.0e-48)
]

# LEP Chargino/Neutralino Limits (approximated from PDG 2024)
# For vector portal dark matter, LEP limits are typically on the kinetic mixing parameter epsilon
# or the dark photon mass. These are approximate exclusion boundaries.
LEP_LIMITS = [
    # (m_V [MeV], epsilon_max)
    (10.0, 1.5e-3),
    (20.0, 8.0e-4),
    (50.0, 3.0e-4),
    (100.0, 1.5e-4),
    (200.0, 8.0e-5),
    (500.0, 3.0e-5),
    (1000.0, 1.5e-5),
    (2000.0, 8.0e-6),
    (5000.0, 3.0e-6),
    (10000.0, 1.5e-6)
]

def get_planck_constants() -> Dict[str, float]:
    """Return Planck 2018 cosmological constants."""
    return PLANCK_2018_CONSTANTS.copy()

def get_xenon1t_limits() -> List[Tuple[float, float]]:
    """Return Xenon1T 2018 spin-independent cross-section limits."""
    return XENON1T_LIMITS.copy()

def get_lep_limits() -> List[Tuple[float, float]]:
    """Return LEP exclusion limits for dark photon parameters."""
    return LEP_LIMITS.copy()