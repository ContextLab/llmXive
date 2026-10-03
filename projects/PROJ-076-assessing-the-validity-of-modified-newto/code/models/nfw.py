"""
NFW (Navarro-Frenk-White) dark matter halo models.
Implements the NFW profile with a Gaussian prior on concentration based on baryonic mass.
"""
import numpy as np
from typing import Tuple, Optional

# Gravitational constant in units of (km/s)^2 * kpc / (1e10 Msun)
# G = 4.302e-6 (km/s)^2 kpc / Msun
# To match typical astrophysical units where mass is in 1e10 Msun and radius in kpc:
# G_unit = 4.302e-6 * 1e10 = 43.02 (km/s)^2 kpc / (1e10 Msun)
G_UNIT = 43.02

def nfw_enclosed_mass(r: np.ndarray, rs: float, rho_s: float) -> np.ndarray:
    """
    Calculate the enclosed mass of an NFW halo within radius r.

    M(<r) = 4 * pi * rho_s * rs^3 * [ln(1 + r/rs) - (r/rs) / (1 + r/rs)]

    Args:
        r: Radial distance array (kpc).
        rs: Scale radius (kpc).
        rho_s: Characteristic density (1e10 Msun / kpc^3).

    Returns:
        Enclosed mass array (1e10 Msun).
    """
    x = r / rs
    # Avoid division by zero at r=0
    x_safe = np.where(x == 0, 1e-10, x)
    factor = np.log(1 + x_safe) - x_safe / (1 + x_safe)
    return 4.0 * np.pi * rho_s * (rs ** 3) * factor

def nfw_circular_velocity(r: np.ndarray, rs: float, rho_s: float) -> np.ndarray:
    """
    Calculate the circular velocity of an NFW halo.

    v^2 = G * M(<r) / r

    Args:
        r: Radial distance array (kpc).
        rs: Scale radius (kpc).
        rho_s: Characteristic density (1e10 Msun / kpc^3).

    Returns:
        Circular velocity squared array ((km/s)^2).
    """
    M = nfw_enclosed_mass(r, rs, rho_s)
    # Handle r=0 case to avoid division by zero
    v_sq = np.where(r == 0, 0.0, G_UNIT * M / r)
    return v_sq

def nfw_concentration_prior(c: float, M_baryon: float, alpha: float = 0.24) -> float:
    """
    Calculate the log-probability of the Gaussian prior for concentration c.

    The prior is based on the relation c ~ M_baryon^alpha (FR-005).
    We assume a log-normal distribution around the expected value.

    Args:
        c: Concentration parameter (dimensionless).
        M_baryon: Baryonic mass (1e10 Msun).
        alpha: Scaling exponent (default 0.24 as per corrected FR-005).

    Returns:
        Log-probability of the prior (scalar).
    """
    if c <= 0:
        return -np.inf

    # Expected concentration: c_expected = c_0 * (M_baryon / M_0)^alpha
    # Normalized to 1e10 solar masses as per context
    c_expected = 10.0 * (M_baryon / 1.0) ** alpha
    
    sigma_log = 0.2  # Logarithmic width (standard deviation in log space)

    log_c = np.log(c)
    log_c_expected = np.log(c_expected)

    # Gaussian in log space: -0.5 * ((x - mu) / sigma)^2
    return -0.5 * ((log_c - log_c_expected) / sigma_log) ** 2

def nfw_with_baryons(r: np.ndarray, rs: float, rho_s: float, M_baryon: float, r_b: float) -> np.ndarray:
    """
    Calculate total circular velocity squared including NFW halo and baryons.

    v^2_total = v^2_NFW + v^2_baryons

    Baryons are approximated as a Plummer sphere or simple point mass for stability.
    v^2_baryon = G * M_baryon / sqrt(r^2 + r_b^2)

    Args:
        r: Radial distance array (kpc).
        rs: NFW scale radius (kpc).
        rho_s: NFW characteristic density (1e10 Msun / kpc^3).
        M_baryon: Baryonic mass (1e10 Msun).
        r_b: Baryonic scale radius (kpc) for softening.

    Returns:
        Total circular velocity squared array ((km/s)^2).
    """
    v_sq_nfw = nfw_circular_velocity(r, rs, rho_s)

    # Baryonic contribution using a softened point mass (Plummer-like) to avoid singularity at r=0
    # v^2 = G * M / sqrt(r^2 + r_b^2)
    denom = np.sqrt(r ** 2 + r_b ** 2)
    v_sq_baryon = np.where(denom == 0, 0.0, G_UNIT * M_baryon / denom)

    return v_sq_nfw + v_sq_baryon

def nfw_model(r: np.ndarray, rs: float, rho_s: float, M_baryon: float, r_b: float, c: float) -> np.ndarray:
    """
    Full NFW model with concentration prior and baryonic component.

    This function computes the total circular velocity squared.
    Note: The concentration `c` is used to constrain the fit via the prior (in the fitting engine),
    but here it is passed to ensure the parameter signature matches the fitting interface.
    The physical velocity is derived from rs and rho_s (and baryons).

    Args:
        r: Radial distance array (kpc).
        rs: Scale radius (kpc).
        rho_s: Characteristic density (1e10 Msun / kpc^3).
        M_baryon: Baryonic mass (1e10 Msun).
        r_b: Baryonic scale radius (kpc).
        c: Concentration parameter (dimensionless).

    Returns:
        Total circular velocity squared array ((km/s)^2).
    """
    # The velocity is determined by the mass distribution (rs, rho_s, M_baryon, r_b)
    # The concentration `c` is primarily used in the prior calculation during fitting.
    return nfw_with_baryons(r, rs, rho_s, M_baryon, r_b)

def nfw_model_params() -> dict:
    """
    Return default parameters for NFW model fitting.

    Returns:
        Dictionary of default parameters with bounds for curve_fit.
    """
    return {
        "rs": 10.0,      # kpc
        "rho_s": 0.1,    # 1e10 Msun / kpc^3
        "M_baryon": 1.0, # 1e10 Msun (often fixed or scaled by M/L)
        "r_b": 3.0,      # kpc
        "c": 10.0,       # dimensionless
    }

def nfw_prior_log_prob(params: dict, M_baryon_obs: float) -> float:
    """
    Calculate the total log-prior probability for NFW parameters.

    Currently implements the Gaussian prior on concentration c ~ M_baryon^alpha.

    Args:
        params: Dictionary containing 'c' and potentially others.
        M_baryon_obs: Observed baryonic mass (1e10 Msun).

    Returns:
        Total log-prior probability.
    """
    c = params.get('c', 10.0)
    # Alpha fixed at 0.24 per corrected FR-005
    return nfw_concentration_prior(c, M_baryon_obs, alpha=0.24)
