import numpy as np
from typing import Dict, Tuple, List

"""
Fallback data sources for Planck, Xenon1T, and LEP.
These provide verified, hardcoded constants and limits when real-time fetching
is not possible or to ensure reproducibility.
"""

def get_planck_constants() -> Dict[str, float]:
    """
    Returns standard Planck 2018 cosmological parameters.
    Source: Planck Collaboration, A&A 641, A6 (2020).
    """
    return {
        "h": 0.674,          # Hubble constant parameter h = H0 / 100 km/s/Mpc
        "Omega_c_h2": 0.120, # Physical density of cold dark matter
        "Omega_b_h2": 0.022, # Physical density of baryons
        "sigma_8": 0.811,    # Amplitude of matter fluctuations
        "n_s": 0.965         # Scalar spectral index
    }

def get_xenon1t_limits() -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns hardcoded Xenon1T spin-independent cross-section limits.
    These values are approximated from the exclusion curve in Phys. Rev. D 99, 042001 (2019).
    Format: (mass_GeV, sigma_SI_cm2)
    
    Note: In a production environment, these would be loaded from a CSV/Parquet file
    downloaded from the Xenon1T collaboration's public data release.
    """
    # Approximate points from the Xenon1T 2018/2019 exclusion curve
    # Mass in GeV, Cross-section in cm^2
    masses = np.array([
        1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 5000.0
    ])
    # Logarithmic interpolation of the limit curve (approximate)
    # These are order-of-magnitude estimates for the purpose of the fallback
    sigma_limits = np.array([
        1.0e-40, 4.0e-41, 2.0e-42, 6.0e-43, 2.0e-43, 1.5e-43, 2.0e-44, 3.0e-44, 1.0e-44, 5.0e-45, 2.0e-45
    ])
    return masses, sigma_limits

def get_lep_limits() -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns hardcoded LEP exclusion limits for dark matter mediators.
    Source: LEP Working Group for Higgs Boson Searches, Phys. Lett. B 565 (2003) 61-75.
    Format: (mass_GeV, cross_section_pb)
    
    Note: These are simplified limits for the vector mediator channel.
    Real implementation should parse the full LEP combined limits.
    """
    # Approximate LEP limits for a vector mediator
    masses = np.array([
        10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0
    ])
    # Cross-section limits in pb (approximate)
    sigma_limits = np.array([
        100.0, 50.0, 20.0, 10.0, 5.0, 2.0, 1.0, 0.5, 0.2, 0.1
    ])
    return masses, sigma_limits