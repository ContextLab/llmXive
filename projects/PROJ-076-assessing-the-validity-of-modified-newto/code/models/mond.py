"""
Modified Newtonian Dynamics (MOND) models.

Implements the 'simple' interpolating function as specified in FR-004 and Plan Summary.
Formula: a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0)
"""
import numpy as np
from typing import Union, Tuple, Optional

# Default critical acceleration scale (m/s^2) per specification
DEFAULT_A0 = 1.2e-10
# Gravitational constant (m^3 kg^-1 s^-2)
G = 6.67430e-11

def mond_simple(r: Union[np.ndarray, float], a0: float = DEFAULT_A0, M: float = 1.0) -> Union[np.ndarray, float]:
    """
    Calculate the circular velocity squared (v^2) for the MOND 'simple' interpolating function.
    
    The 'simple' interpolating function implies the acceleration relation:
        a = a_N / 2 + sqrt((a_N / 2)^2 + a_N * a0)
    
    Where:
        a_N = G * M / r^2 (Newtonian acceleration)
        v^2 = r * a
    
    Args:
        r: Radial distance (in meters or consistent units).
        a0: Critical acceleration scale (default 1.2e-10 m/s^2).
        M: Total baryonic mass (in kg or consistent units).
    
    Returns:
        Circular velocity squared (v^2) at radius r.
    """
    r = np.asarray(r, dtype=np.float64)
    # Avoid division by zero at r=0
    r_safe = np.where(r == 0, 1e-10, r)
    
    # Newtonian acceleration: a_N = G * M / r^2
    a_N = G * M / (r_safe ** 2)

    # MOND 'simple' interpolating function logic
    # a = a_N / 2 + sqrt((a_N / 2)^2 + a_N * a0)
    term1 = a_N / 2.0
    term2 = np.sqrt(term1 ** 2 + a_N * a0)
    a_mond = term1 + term2

    return r * a_mond

def mond_simple_velocity(r: Union[np.ndarray, float], a0: float = DEFAULT_A0, M: float = 1.0) -> Union[np.ndarray, float]:
    """
    Calculate the circular velocity (v) for the MOND 'simple' interpolating function.
    
    This is the square root of mond_simple (v = sqrt(r * a)).
    
    Args:
        r: Radial distance (in meters or consistent units).
        a0: Critical acceleration scale (default 1.2e-10 m/s^2).
        M: Total baryonic mass (in kg or consistent units).
    
    Returns:
        Circular velocity (v) at radius r.
    """
    v_squared = mond_simple(r, a0, M)
    # Ensure non-negative due to numerical precision
    return np.sqrt(np.maximum(v_squared, 0.0))

def mond_simple_acceleration(r: Union[np.ndarray, float], a0: float = DEFAULT_A0, M: float = 1.0) -> Union[np.ndarray, float]:
    """
    Calculate the acceleration (a) for the MOND 'simple' interpolating function.
    
    Args:
        r: Radial distance (in meters or consistent units).
        a0: Critical acceleration scale (default 1.2e-10 m/s^2).
        M: Total baryonic mass (in kg or consistent units).
    
    Returns:
        Acceleration (a) at radius r.
    """
    r = np.asarray(r, dtype=np.float64)
    r_safe = np.where(r == 0, 1e-10, r)
    
    a_N = G * M / (r_safe ** 2)

    term1 = a_N / 2.0
    term2 = np.sqrt(term1 ** 2 + a_N * a0)
    return term1 + term2

def mond_simple_model(r: Union[np.ndarray, float], M_l: float, a0: float = DEFAULT_A0) -> Union[np.ndarray, float]:
    """
    MOND 'simple' model wrapper for curve fitting (scipy.optimize.curve_fit).
    
    This function implements the interface required by FR-004, including M/L (mass-to-light ratio)
    as a free parameter. In the context of the fitting engine, `M_l` represents the scaling factor
    for the baryonic mass distribution (effectively the total mass M if luminosity is normalized,
    or M = M_l * L).
    
    The model calculates v(r) using the 'simple' interpolating function:
        a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0)
        v = sqrt(r * a)
    
    Args:
        r: Radial distance (meters).
        M_l: Mass-to-light ratio (or effective total mass) parameter.
             This is the free parameter to be fitted.
        a0: Critical acceleration scale (m/s^2). Defaults to 1.2e-10.
    
    Returns:
        Circular velocity (v) in consistent units (m/s).
    """
    # Interpret M_l as the total effective mass M for the calculation.
    # The fitting engine (fit.py) will handle unit conversions (e.g., km/s, kpc)
    # before calling this, or this function assumes SI units.
    return mond_simple_velocity(r, a0, M_l)

def mond_simple_model_with_params(r: Union[np.ndarray, float], M_l: float, a0: float = DEFAULT_A0) -> Union[np.ndarray, float]:
    """
    Alternative signature allowing a0 to be a free parameter if needed,
    though the task specification fixes a0=1.2e-10.
    
    Args:
        r: Radial distance.
        M_l: Mass parameter (M/L).
        a0: Critical acceleration scale.
    
    Returns:
        Circular velocity.
    """
    return mond_simple_velocity(r, a0, M_l)