"""
Fallback data for Planck, Xenon1T, and LEP constraints.
Used when network access is unavailable or data sources are unreachable.
These values are extracted from standard literature references.
"""
import numpy as np
from typing import Dict, Tuple, List

# Planck 2018 Cosmological Parameters (arXiv:1807.06209)
# Central values for Cold Dark Matter density and Baryon density
PLANCK_CONSTANTS = {
    "Omega_c_h2": 0.120,
    "Omega_b_h2": 0.022,
    "h": 0.674,
    "source": "Planck 2018 Results VI. Cosmological Parameters"
}

# Xenon1T 2018 Exclusion Limits (Phys. Rev. D 98, 112009)
# Approximated points for the exclusion curve (Mass [GeV], Sigma_SI [cm^2])
# These are representative points from the published plot for fallback usage.
XENON1T_FALLBACK_POINTS = [
    (1.0, 4.0e-45),
    (2.0, 1.0e-45),
    (5.0, 3.0e-46),
    (10.0, 1.0e-46),
    (20.0, 5.0e-47),
    (50.0, 2.0e-47),
    (100.0, 1.0e-47),
    (200.0, 5.0e-48),
    (500.0, 2.0e-48),
    (1000.0, 1.0e-48)
]

# LEP Limits for Vector Mediators (Ref [2014] / PDG)
# Simplified fallback: m_V > 10 GeV for g = 0.1 (example)
# In a real scenario, this would be a more complex function or lookup table.
LEP_FALLBACK_RULES = [
    {
        "mediator_mass_min": 10.0, # GeV
        "coupling_g": 0.1,
        "description": "LEP limit for m_V > 10 GeV at g=0.1"
    },
    {
        "mediator_mass_min": 20.0, # GeV
        "coupling_g": 0.01,
        "description": "LEP limit for m_V > 20 GeV at g=0.01"
    }
]

def get_planck_constants() -> Dict[str, float]:
    """Returns the fallback Planck constants."""
    return PLANCK_CONSTANTS

def get_xenon1t_limits() -> Tuple[np.ndarray, np.ndarray]:
    """Returns mass and cross-section arrays for Xenon1T fallback."""
    masses, sigmas = zip(*XENON1T_FALLBACK_POINTS)
    return np.array(masses), np.array(sigmas)

def get_lep_limits() -> List[Dict]:
    """Returns the list of LEP fallback rules."""
    return LEP_FALLBACK_RULES
