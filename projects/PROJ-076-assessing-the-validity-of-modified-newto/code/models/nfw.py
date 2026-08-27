"""
NFW (Navarro-Frenk-White) dark matter halo model implementation.

This module implements the NFW profile for fitting galaxy rotation curves,
including a concentration-mass prior where c ~ M_baryon^α with α < 0.
"""

import numpy as np
from typing import Tuple, Optional

# Constants
G = 4.302e-6  # Gravitational constant in kpc (km/s)^2 / Msun
c_min = 1.0
c_max = 50.0
alpha_prior = -0.1  # Negative scaling exponent for c ~ M_baryon^α

def nfw_enclosed_mass(r: np.ndarray, v_c: float, r_s: float) -> np.ndarray:
    """
    Calculate the enclosed mass of an NFW halo at radius r.

    The NFW density profile is: rho(r) = rho_s / ((r/r_s) * (1 + r/r_s)^2)

    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc
    v_c : float
        Circular velocity scale in km/s
    r_s : float
        Scale radius in kpc

    Returns
    -------
    np.ndarray
        Enclosed mass in Msun
    """
    x = r / r_s
    # Avoid division by zero at r=0
    x_safe = np.where(x == 0, 1e-10, x)

    # Enclosed mass for NFW profile: M(<r) = 4 * pi * rho_s * r_s^3 * (ln(1+x) - x/(1+x))
    # Using v_c^2 = G * M(<r) / r, we can express in terms of v_c and r_s
    # M(<r) = (v_c^2 * r) / G * f(x) where f(x) accounts for the profile shape
    # For NFW: f(x) = x^2 / (ln(1+x) - x/(1+x)) * (ln(1+x) - x/(1+x)) = x^2
    # Actually, let's use the direct form:
    # M(<r) = 4 * pi * rho_s * r_s^3 * (ln(1+x) - x/(1+x))
    # And v_c^2 = G * M(<r) / r = G * 4 * pi * rho_s * r_s^3 / r * (ln(1+x) - x/(1+x))
    # At large r, v_c^2 approaches a constant related to the total mass

    # Simplified: use the relation v_c^2 = G * M(<r) / r
    # For NFW, the circular velocity is:
    # v_c^2(r) = v_max^2 * (ln(1+c*r/r_vir) - (c*r/r_vir)/(1+c*r/r_vir)) / (ln(1+c) - c/(1+c)) * (r_vir/r)
    # But we parameterize with v_c (velocity scale) and r_s (scale radius)

    # Standard NFW circular velocity formula:
    # v_c^2(r) = (G * M_vir / r_vir) * [ln(1+c*x) - c*x/(1+c*x)] / [ln(1+c) - c/(1+c)] * (1/x)
    # where x = r / r_vir, c = r_vir / r_s

    # Alternative parameterization using v_c (characteristic velocity) and r_s:
    # v_c^2(r) = v_c^2 * [ln(1+r/r_s) - (r/r_s)/(1+r/r_s)] / (r/r_s) / [ln(1+c) - c/(1+c)] * c
    # This is complex, so we use a simpler form:

    # Direct calculation from density profile:
    # rho(r) = rho_crit * delta_c / (x * (1+x)^2)
    # M(<r) = 4 * pi * rho_crit * delta_c * r_s^3 * (ln(1+x) - x/(1+x))
    # v_c^2(r) = G * M(<r) / r

    # Using v_c as the velocity at r_s:
    # v_c^2 = G * M(<r_s) / r_s = G * 4 * pi * rho_crit * delta_c * r_s^2 * (ln(2) - 1/2)
    # So: 4 * pi * rho_crit * delta_c = v_c^2 / (G * r_s^2 * (ln(2) - 0.5))

    ln2_minus_half = np.log(2) - 0.5
    factor = v_c**2 / (G * r_s**2 * ln2_minus_half)

    # Enclosed mass
    mass = factor * r_s**3 * (np.log(1 + x_safe) - x_safe / (1 + x_safe))

    return mass

def nfw_circular_velocity(r: np.ndarray, v_c: float, r_s: float, c: float = 10.0) -> np.ndarray:
    """
    Calculate the circular velocity contribution from an NFW dark matter halo.

    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc
    v_c : float
        Circular velocity scale at r_s (km/s)
    r_s : float
        Scale radius (kpc)
    c : float, optional
        Concentration parameter (default: 10.0)

    Returns
    -------
    np.ndarray
        Circular velocity in km/s
    """
    x = r / r_s
    x_safe = np.where(x == 0, 1e-10, x)

    # NFW circular velocity formula
    # v_c^2(r) = (G * M(<r)) / r
    # M(<r) for NFW: 4 * pi * rho_s * r_s^3 * (ln(1+x) - x/(1+x))
    # We parameterize using v_c at r_s

    ln2_minus_half = np.log(2) - 0.5
    factor = v_c**2 / (G * r_s * ln2_minus_half)

    # v_c^2(r) = factor * r_s^2 * (ln(1+x) - x/(1+x)) / x
    v_squared = factor * r_s * (np.log(1 + x_safe) - x_safe / (1 + x_safe)) / x_safe

    # Ensure non-negative values (numerical stability)
    v_squared = np.maximum(v_squared, 0)

    return np.sqrt(v_squared)

def nfw_with_baryons(
    r: np.ndarray,
    v_dm: float,
    r_s: float,
    v_baryon: float,
    c: float = 10.0,
    m_l_ratio: float = 0.5
) -> np.ndarray:
    """
    Calculate total circular velocity including NFW dark matter and baryonic components.

    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc
    v_dm : float
        Dark matter velocity scale at r_s (km/s)
    r_s : float
        Dark matter scale radius (kpc)
    v_baryon : float
        Baryonic velocity scale (km/s)
    c : float, optional
        Concentration parameter (default: 10.0)
    m_l_ratio : float, optional
        Mass-to-light ratio for baryonic component (default: 0.5)

    Returns
    -------
    np.ndarray
        Total circular velocity in km/s
    """
    v_dm_contrib = nfw_circular_velocity(r, v_dm, r_s, c)

    # Simple baryonic component: exponential disk approximation
    # v_baryon^2(r) = v_baryon^2 * (1 - exp(-r/r_d)) where r_d is disk scale length
    # Using a simplified form: v_baryon * sqrt(1 - exp(-r/r_d))
    # Assume r_d ~ r_s / 3 for typical galaxies
    r_d = r_s / 3.0
    r_safe = np.where(r == 0, 1e-10, r)
    v_baryon_contrib = v_baryon * m_l_ratio * np.sqrt(1 - np.exp(-r_safe / r_d))

    # Combine in quadrature
    v_total = np.sqrt(v_dm_contrib**2 + v_baryon_contrib**2)

    return v_total

def nfw_concentration_prior(m_baryon: float, alpha: float = alpha_prior) -> float:
    """
    Calculate the expected concentration parameter based on baryonic mass.

    Prior: c ~ M_baryon^α where α is negative (more massive galaxies have lower concentration)

    Parameters
    ----------
    m_baryon : float
        Baryonic mass in Msun
    alpha : float, optional
        Scaling exponent (default: -0.1)

    Returns
    -------
    float
        Expected concentration parameter
    """
    if m_baryon <= 0:
        return c_min

    c_expected = 10.0 * (m_baryon / 1e10) ** alpha

    # Clamp to reasonable range
    return np.clip(c_expected, c_min, c_max)

def nfw_model(
    r: np.ndarray,
    v_dm: float,
    r_s: float,
    v_baryon: float,
    m_baryon: float,
    m_l_ratio: float = 0.5,
    alpha: float = alpha_prior
) -> np.ndarray:
    """
    Full NFW model with concentration prior based on baryonic mass.

    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc
    v_dm : float
        Dark matter velocity scale at r_s (km/s)
    r_s : float
        Dark matter scale radius (kpc)
    v_baryon : float
        Baryonic velocity scale (km/s)
    m_baryon : float
        Baryonic mass in Msun (used for concentration prior)
    m_l_ratio : float, optional
        Mass-to-light ratio (default: 0.5)
    alpha : float, optional
        Concentration-mass scaling exponent (default: -0.1)

    Returns
    -------
    np.ndarray
        Predicted circular velocity in km/s
    """
    c = nfw_concentration_prior(m_baryon, alpha)
    return nfw_with_baryons(r, v_dm, r_s, v_baryon, c, m_l_ratio)

def nfw_model_params(
    r: np.ndarray,
    v_dm: float,
    r_s: float,
    v_baryon: float,
    m_l_ratio: float
) -> np.ndarray:
    """
    NFW model with fixed concentration (for simpler fitting).

    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc
    v_dm : float
        Dark matter velocity scale at r_s (km/s)
    r_s : float
        Dark matter scale radius (kpc)
    v_baryon : float
        Baryonic velocity scale (km/s)
    m_l_ratio : float
        Mass-to-light ratio

    Returns
    -------
    np.ndarray
        Predicted circular velocity in km/s
    """
    c = 10.0  # Fixed concentration
    return nfw_with_baryons(r, v_dm, r_s, v_baryon, c, m_l_ratio)
