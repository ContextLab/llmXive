"""
Modified Newtonian Dynamics (MOND) models.
"""
import numpy as np
from typing import Union, Tuple, Optional

# Default critical acceleration scale (m/s^2)
DEFAULT_A0 = 1.2e-10
# Gravitational constant (m^3 kg^-1 s^-2)
G = 6.67430e-11

def mond_simple(r: Union[np.ndarray, float], a0: float = DEFAULT_A0, M: float = 1.0) -> Union[np.ndarray, float]:
    """
    Calculate the circular velocity squared for the MOND 'simple' interpolating function.

    The 'simple' interpolating function is defined as:
        mu(x) = x / (1 + x)
    where x = a / a0.

    The acceleration relation is:
        a = a_N / 2 + sqrt((a_N / 2)^2 + a_N * a0)

    This function returns v^2 = r * a.

    Args:
        r: Radial distance (in meters or consistent units).
        a0: Critical acceleration scale (default 1.2e-10 m/s^2).
        M: Total baryonic mass (in kg or consistent units).

    Returns:
        Circular velocity squared (v^2) at radius r.
    """
    r = np.asarray(r, dtype=np.float64)
    # Avoid division by zero
    r_safe = np.where(r == 0, 1e-10, r)
    
    a_N = G * M / (r_safe ** 2)

    # MOND 'simple' interpolating function logic
    # a = a_N / 2 + sqrt((a_N / 2)^2 + a_N * a0)
    term1 = a_N / 2.0
    term2 = np.sqrt(term1 ** 2 + a_N * a0)
    a_mond = term1 + term2

    return r * a_mond

def mond_simple_velocity(r: Union[np.ndarray, float], a0: float = DEFAULT_A0, M: float = 1.0) -> Union[np.ndarray, float]:
    """
    Calculate the circular velocity for the MOND 'simple' interpolating function.

    This is the square root of mond_simple.

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
    Calculate the acceleration for the MOND 'simple' interpolating function.

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
    MOND 'simple' model wrapper for curve fitting.
    
    This function is designed to be used with scipy.optimize.curve_fit.
    It takes radial distance and a mass-to-light ratio (M_l) as parameters.
    The total mass M is assumed to be M_l * L, where L is a fixed luminosity
    or the mass is directly scaled by M_l. For fitting purposes, we treat M_l
    as the total mass parameter if the input data is normalized, or we assume
    a fixed luminosity L=1.0 for the model definition.
    
    In the context of the fitting engine (fit.py), this will likely be called
    with M_l representing the total baryonic mass directly, or scaled by a 
    known luminosity. Here, we interpret M_l as the effective mass M for the
    calculation to keep the interface simple for curve_fit (one free parameter).
    
    Args:
        r: Radial distance (meters).
        M_l: Mass-to-light ratio (or effective mass) parameter (kg or solar units).
        a0: Critical acceleration scale (m/s^2).
    
    Returns:
        Circular velocity (v) in consistent units (m/s).
    """
    # If M_l is meant to be M/L and we have a fixed L, we would multiply by L.
    # Assuming for the fitting interface that M_l is the total mass M to be fitted.
    # If the data is in km/s and kpc, unit conversion must happen before calling this
    # or inside the fitting wrapper. We assume SI units here.
    return mond_simple_velocity(r, a0, M_l)

def mond_simple_model_with_params(r: Union[np.ndarray, float], M_l: float, a0: float = DEFAULT_A0) -> Union[np.ndarray, float]:
    """
    Alternative signature allowing a0 to be a free parameter if needed,
    though the task specifies a0=1.2e-10.
    
    Args:
        r: Radial distance.
        M_l: Mass parameter.
        a0: Critical acceleration scale.
    
    Returns:
        Circular velocity.
    """
    return mond_simple_velocity(r, a0, M_l)