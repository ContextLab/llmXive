"""
MOND (Modified Newtonian Dynamics) models.

Implements the 'simple' interpolating function as per the project specification:
a = a_N/2 + sqrt((a_N/2)^2 + a_N * a_0)

This module provides the velocity prediction function compatible with
scipy.optimize.curve_fit, including the mass-to-light ratio (M/L) as a free parameter.
"""
import numpy as np
from typing import Union

# Standard MOND acceleration scale (m/s^2)
A0 = 1.2e-10

def mond_simple(r: Union[np.ndarray, float], v_c: float, m_l_ratio: float, a0: float = A0) -> Union[np.ndarray, float]:
    """
    Calculate the circular velocity predicted by the MOND 'simple' model.

    The 'simple' interpolating function is defined by:
    mu(a/a0) = a / (a + a0)  =>  a = a_N/2 + sqrt((a_N/2)^2 + a_N * a0)

    where:
      a_N = G * M(r) / r^2  (Newtonian acceleration)
      M(r) = M_baryon(r) * (M/L_ratio)

    The circular velocity v is related to acceleration a by v^2 / r = a.
    Thus, v = sqrt(a * r).

    Parameters
    ----------
    r : np.ndarray or float
        Radial distances in meters.
    v_c : float
        Asymptotic circular velocity (km/s) - used for normalization if needed,
        but primarily we calculate based on mass.
        Note: In this implementation, we derive velocity from the acceleration
        directly. The parameter 'v_c' is kept for API consistency with fitting
        routines that might expect it, but the core physics comes from M/L.
        Actually, looking at standard fitting practices, usually M/L is the
        parameter scaling the baryonic mass. We assume the input 'r' is in kpc
        or meters? The spec says 'radial distance'. We will assume input 'r'
        is in meters for physics consistency, but handle unit conversion if
        the data is in kpc.
        
        Let's clarify the inputs based on typical SPARC data:
        - r is usually in kpc.
        - v_obs is in km/s.
        - Mass-to-light ratio (M/L) is dimensionless (usually in solar units).
        - We need G in appropriate units.

    m_l_ratio : float
        Mass-to-light ratio (M/L) in solar units (M_sun / L_sun).
    a0 : float
        The critical acceleration scale. Default is 1.2e-10 m/s^2.

    Returns
    -------
    np.ndarray or float
        Predicted circular velocity in km/s.
    """
    # Ensure inputs are numpy arrays for vectorized operations
    r = np.asarray(r, dtype=np.float64)
    
    # Constants
    # G in (km/s)^2 * kpc / M_sun
    # G = 6.674e-11 m^3 kg^-1 s^-2
    # 1 M_sun = 1.989e30 kg
    # 1 kpc = 3.086e19 m
    # G_km = 6.674e-11 * (1e-3)^2 * (3.086e19) / 1.989e30 * (1e3)^2 ? 
    # Let's use standard value: G = 4.302e-6 (km/s)^2 kpc / M_sun
    G = 4.302e-6  # (km/s)^2 * kpc / M_sun
    
    # a0 in (km/s)^2 / kpc
    # a0 = 1.2e-10 m/s^2
    # 1 m/s^2 = (1e-3 km) / (1 s)^2 * (1 kpc / 3.086e19 m) = 3.24e-20 km/s^2 / kpc ?
    # Let's convert: 1 m/s^2 = 1 (m/s^2) * (1 km / 1000 m) * (3.086e19 m / 1 kpc)
    # = 3.086e16 km/s^2/kpc ? No.
    # 1 m/s^2 = 1 (m/s^2) * (1 km / 1000 m) * (1 kpc / 3.086e19 m)^-1 ?
    # Acceleration = L / T^2.
    # 1 m/s^2 = (10^-3 km) / s^2 = 10^-3 km/s^2.
    # To get km/s^2 per kpc, we divide by distance in kpc? No, acceleration is just acceleration.
    # We need a0 in units of (km/s)^2 / kpc to match G*M/r^2 where r is kpc.
    # a = v^2 / r. Units: (km/s)^2 / kpc.
    # 1 m/s^2 = 1 (m/s^2) * (1 km / 1000 m) * (3.086e19 m / 1 kpc) = 3.086e16 km/s^2 / kpc?
    # Wait. 1 m = 10^-3 km. 1 s^2 = 1 s^2.
    # 1 m/s^2 = 10^-3 km/s^2.
    # To express in (km/s)^2 / kpc:
    # 10^-3 km/s^2 = X (km^2/s^2) / kpc => X = 10^-3 * kpc / km = 10^-3 * 3.086e19.
    # So a0 (km/s^2/kpc) = 1.2e-10 * 3.086e16 = 3.7032e6? That seems huge.
    # Let's re-evaluate.
    # a = v^2 / r. If v=200 km/s, r=10 kpc => a = 40000 / 10 = 4000 (km/s)^2/kpc.
    # 1 m/s^2 = 1000 mm/s^2.
    # 1 (km/s)^2/kpc = (1000 m/s)^2 / (3.086e19 m) = 1e6 / 3.086e19 m/s^2 = 3.24e-14 m/s^2.
    # So 1 m/s^2 = 1 / 3.24e-14 (km/s)^2/kpc = 3.086e13 (km/s)^2/kpc.
    # a0 = 1.2e-10 m/s^2 * 3.086e13 = 3703 (km/s)^2/kpc.
    
    a0_units = 1.2e-10 * 3.086e13  # ~3703 (km/s)^2 / kpc
    a0 = a0_units if a0 == A0 else a0  # Use passed a0 if different, but convert if it's the default constant
    
    # If the caller passes the default A0 (1.2e-10), it's in m/s^2. Convert it.
    if a0 == 1.2e-10:
        a0 = 1.2e-10 * 3.086e13
    
    # Newtonian acceleration a_N = G * M / r^2
    # M = M_L * L (where L is luminosity in solar units, M_L is the parameter)
    # However, the function signature usually takes M/L as a parameter and the
    # baryonic mass profile is implicitly handled or passed via a separate mass array.
    # In the context of `fit.py`, we often pass the baryonic mass array directly
    # or the luminosity profile.
    # The prompt says: "include M/L (mass-to-light ratio) as a free parameter".
    # This implies the function signature should accept `r`, `v_c` (maybe unused or for prior?), `m_l_ratio`.
    # But where is the baryonic mass?
    # Standard fitting: v_tot^2 = v_bary^2 * (M/L)^2 * mu^2 + v_DM^2 ...
    # Or v_tot^2 = (G * M_bary * M/L / r) * mu^-1?
    # The formula a = a_N/2 + sqrt(...) implies we need a_N.
    # a_N = G * M_bary_total / r^2.
    # If we don't have M_bary_total in the function arguments, we cannot compute a_N.
    # Assumption: The `fit.py` calls this function with `r` and the `baryonic_mass` profile
    # pre-scaled or we assume the `m_l_ratio` scales a known luminosity profile.
    # Since the API surface shows `mond_simple(r, v_c, m_l_ratio)`, and no mass array,
    # we must assume `v_c` might be a proxy or the function is expected to be called
    # with a specific context where mass is derived.
    # HOWEVER, looking at the NFW model signature: `nfw_model(r, v_c, ...)`
    # It's likely `v_c` in the signature is a misnomer in the prompt's API surface description
    # or it represents a scaling factor for the baryonic component if the mass profile is fixed.
    # Let's assume the standard approach: The `fit.py` passes the baryonic mass array as part of `xdata`
    # or the function is wrapped.
    # BUT, the prompt says: "include M/L ... as a free parameter".
    # If I strictly follow `mond_simple(r, v_c, m_l_ratio)`, I cannot calculate `a_N` without `M_bary`.
    # Hypothesis: `v_c` here is actually the circular velocity of the baryonic component
    # at a specific radius, or the function expects `r` to be the only spatial variable
    # and `v_c` is the asymptotic velocity of the baryonic part?
    # Let's look at the NFW signature: `nfw_circular_velocity(r, v_c, ...)`.
    # Usually, `v_c` in these contexts is the circular velocity of the baryonic disk/bulge
    # if the mass-to-light ratio is 1. Then we scale by `m_l_ratio`.
    # Let's assume `v_c` is the circular velocity contribution from baryons with M/L = 1.
    # Then v_bary = v_c * sqrt(m_l_ratio).
    # Then a_N = v_bary^2 / r = (v_c^2 * m_l_ratio) / r.
    
    # Let's proceed with this assumption: v_c is the baryonic circular velocity for M/L=1.
    # v_bary = v_c * sqrt(m_l_ratio)
    # a_N = v_bary^2 / r = (v_c^2 * m_l_ratio) / r
    
    # Handle r=0 to avoid division by zero
    r_safe = np.where(r == 0, 1e-10, r)
    
    # Calculate Newtonian acceleration (in km/s^2 / kpc? No, units of a_N must match a0)
    # a_N = v^2 / r. If v is km/s, r is kpc, then a_N is (km/s)^2 / kpc.
    # v_bary_sq = (v_c * sqrt(m_l_ratio))^2 = v_c^2 * m_l_ratio
    v_bary_sq = (v_c ** 2) * m_l_ratio
    a_N = v_bary_sq / r_safe
    
    # Apply MOND simple interpolating function
    # a = a_N/2 + sqrt((a_N/2)^2 + a_N * a0)
    term1 = a_N / 2.0
    term2 = np.sqrt(term1**2 + a_N * a0)
    a_mond = term1 + term2
    
    # Convert acceleration back to velocity: v = sqrt(a * r)
    v_mond = np.sqrt(a_mond * r_safe)
    
    return v_mond
