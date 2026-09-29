"""
NFW (Navarro-Frenk-White) Dark Matter Halo models.

Implements the NFW profile with a concentration prior dependent on baryonic mass.
c ~ M_baryon^alpha, where alpha is a negative scaling exponent.
"""
import numpy as np
from typing import Tuple, Optional

# Gravitational constant in (km/s)^2 * kpc / M_sun
G = 4.302e-6

def nfw_enclosed_mass(r: np.ndarray, v_c: float, c: float, rs: float) -> np.ndarray:
    """
    Calculate the enclosed mass of an NFW halo.
    
    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc.
    v_c : float
        Circular velocity parameter (km/s).
    c : float
        Concentration parameter.
    rs : float
        Scale radius in kpc.
        
    Returns
    -------
    np.ndarray
        Enclosed mass in M_sun.
    """
    x = r / rs
    # NFW density profile: rho(r) = rho_s / (x * (1+x)^2)
    # Enclosed mass: M(r) = 4 * pi * rho_s * rs^3 * (ln(1+x) - x/(1+x))
    # We relate rho_s to v_c and c.
    # v_c^2 = G * M(r) / r. At virial radius R_vir = c * rs.
    # M_vir = v_c^2 * R_vir / G.
    # Also M_vir = 4 * pi * rho_s * rs^3 * f(c), where f(c) = ln(1+c) - c/(1+c).
    # So 4 * pi * rho_s * rs^3 = M_vir / f(c).
    # M(r) = (M_vir / f(c)) * (ln(1+x) - x/(1+x))
    
    f_c = np.log(1 + c) - c / (1 + c)
    M_vir = (v_c ** 2) * (c * rs) / G
    M_r = (M_vir / f_c) * (np.log(1 + x) - x / (1 + x))
    
    return M_r

def nfw_circular_velocity(r: np.ndarray, v_c: float, c: float, rs: float) -> np.ndarray:
    """
    Calculate the circular velocity of an NFW halo.
    
    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc.
    v_c : float
        Circular velocity parameter (km/s).
    c : float
        Concentration parameter.
    rs : float
        Scale radius in kpc.
        
    Returns
    -------
    np.ndarray
        Circular velocity in km/s.
    """
    M_r = nfw_enclosed_mass(r, v_c, c, rs)
    # v = sqrt(G * M / r)
    r_safe = np.where(r == 0, 1e-10, r)
    v = np.sqrt(G * M_r / r_safe)
    return v

def nfw_with_baryons(r: np.ndarray, v_c: float, c: float, rs: float, 
                     m_l_ratio: float, v_bary_c: float) -> np.ndarray:
    """
    Calculate total circular velocity including NFW halo and baryonic components.
    
    Assumes baryonic contribution scales with m_l_ratio.
    v_total^2 = v_halo^2 + (v_bary_c * sqrt(m_l_ratio))^2
    
    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc.
    v_c : float
        Halo circular velocity parameter (km/s).
    c : float
        Concentration parameter.
    rs : float
        Scale radius in kpc.
    m_l_ratio : float
        Mass-to-light ratio for baryons.
    v_bary_c : float
        Circular velocity of baryons at M/L=1 (km/s).
        
    Returns
    -------
    np.ndarray
        Total circular velocity in km/s.
    """
    v_halo = nfw_circular_velocity(r, v_c, c, rs)
    v_bary = v_bary_c * np.sqrt(m_l_ratio)
    v_total = np.sqrt(v_halo**2 + v_bary**2)
    return v_total

def nfw_concentration_prior(m_baryon: float, alpha: float = -0.1) -> float:
    """
    Calculate the expected concentration based on baryonic mass.
    
    c ~ M_baryon^alpha
    
    Parameters
    ----------
    m_baryon : float
        Baryonic mass in M_sun.
    alpha : float
        Scaling exponent (negative).
        
    Returns
    -------
    float
        Expected concentration.
    """
    if m_baryon <= 0:
        return 10.0 # Default fallback
    return 10.0 * (m_baryon / 1e10) ** alpha

def nfw_model(r: np.ndarray, v_c: float, c: float, rs: float, 
              m_l_ratio: float, v_bary_c: float) -> np.ndarray:
    """
    Wrapper for the full NFW model with baryons.
    
    Parameters
    ----------
    r : np.ndarray
        Radial distances in kpc.
    v_c : float
        Halo circular velocity parameter (km/s).
    c : float
        Concentration parameter.
    rs : float
        Scale radius in kpc.
    m_l_ratio : float
        Mass-to-light ratio.
    v_bary_c : float
        Baryonic circular velocity at M/L=1.
        
    Returns
    -------
    np.ndarray
        Predicted circular velocity.
    """
    return nfw_with_baryons(r, v_c, c, rs, m_l_ratio, v_bary_c)

def nfw_model_params() -> dict:
    """
    Return default parameter bounds and names for the NFW model.
    
    Returns
    -------
    dict
        Dictionary with parameter names, bounds, and initial guesses.
    """
    return {
        'names': ['v_c', 'c', 'rs', 'm_l_ratio', 'v_bary_c'],
        'bounds': (
            [0, 1, 0.1, 0.1, 0], # Lower bounds
            [500, 50, 100, 10, 500] # Upper bounds
        ),
        'p0': [200, 10, 10, 1.0, 100] # Initial guesses
    }
