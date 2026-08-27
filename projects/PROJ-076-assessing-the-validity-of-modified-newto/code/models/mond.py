"""
MOND 'simple' model implementation for galaxy rotation curves.

Implements the formula: a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0)
where a_0 = 1.2e-10 m/s^2.

The model includes the Mass-to-Light ratio (M/L) as a free parameter
to scale the baryonic acceleration.
"""
import numpy as np

# MOND acceleration constant (m/s^2)
A0 = 1.2e-10

def mond_simple(r, mass_to_light_ratio, v_circ_scale):
    """
    Calculate the circular velocity predicted by the MOND 'simple' interpolating function.

    The 'simple' interpolating function is defined as:
    mu(x) = x / (1 + x)  =>  a = a_N / 2 + sqrt((a_N / 2)^2 + a_N * a_0)

    Where:
    - a_N is the Newtonian acceleration: G * M_baryon / r^2
    - M_baryon = mass_to_light_ratio * L (luminosity proxy)
    - a_0 is the MOND acceleration constant (1.2e-10 m/s^2)

    The circular velocity v_circ is related to acceleration a by:
    v_circ^2 / r = a  =>  v_circ = sqrt(a * r)

    Parameters
    ----------
    r : array_like
        Radial distances (in kpc).
    mass_to_light_ratio : float
        Mass-to-light ratio (M/L) in solar units (M_sun/L_sun).
        This scales the baryonic mass distribution.
    v_circ_scale : float
        A scaling factor for the Newtonian velocity component (km/s).
        This effectively encapsulates the luminosity and G constants
        into a single fit parameter for the velocity curve amplitude.
        v_circ_Newtonian = v_circ_scale * sqrt(L(r))

    Returns
    -------
    v_pred : ndarray
        Predicted circular velocities (in km/s) at each radial distance.
    """
    r = np.asarray(r, dtype=float)

    # Avoid division by zero or negative radii
    # We assume r > 0 based on data filtering in preprocess.py
    # If r can be 0, we handle it by setting Newtonian acc to 0
    safe_r = np.where(r > 0, r, 1e-10)

    # Newtonian acceleration component proxy:
    # a_N = (v_circ_scale^2) / r  (derived from v^2 = a*r => a = v^2/r)
    # Here v_circ_scale represents the characteristic velocity scale
    # of the baryonic mass distribution.
    # a_N = (v_circ_scale * sqrt(M/L))^2 / r ?
    # Let's stick to the standard form where a_N is proportional to M_baryon / r^2.
    # In the fitting context, we often parameterize the baryonic contribution
    # as v_baryon^2 = (M/L) * v_star^2 + v_gas^2.
    # For this simplified model, we treat 'v_circ_scale' as the amplitude
    # of the Newtonian velocity curve before MOND correction, scaled by M/L.
    # Actually, the prompt asks for M/L as a free parameter.
    # Let's define:
    # a_N = G * M_baryon / r^2
    # We can express M_baryon = (M/L) * L.
    # So a_N is proportional to (M/L).
    # Let's define a reference Newtonian acceleration a_ref = v_scale^2 / r.
    # Then a_N = (M/L) * a_ref? No, that depends on how L scales with r.
    #
    # Standard approach in fitting:
    # v_obs^2 = v_baryon^2 * mu^-1(r)  (approx for deep MOND)
    # More precisely: v^4 / r = G * M_baryon * a_0 (for deep MOND)
    #
    # Let's use the explicit formula provided:
    # a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0)
    # where a_N = G * M_baryon / r^2.
    #
    # We parameterize M_baryon = (M/L) * L_model(r).
    # If we assume the luminosity profile is fixed (from data) and we only fit M/L,
    # then a_N is proportional to M/L.
    # Let a_N_base = G * L_model(r) / r^2. Then a_N = (M/L) * a_N_base.
    #
    # However, the function signature in the task implies a simpler scaling.
    # "include M/L as a free parameter".
    # Let's assume the input `v_circ_scale` represents the velocity scale
    # derived from the luminosity profile (e.g., sqrt(G * L / r)).
    # Then a_N = (v_circ_scale^2 / r) * (M/L).
    # Wait, v^2 = a*r. So a = v^2/r.
    # If v_circ_scale is the velocity corresponding to M/L=1, then
    # v_N^2 = (v_circ_scale * sqrt(M/L))^2 = v_circ_scale^2 * (M/L).
    # Then a_N = v_N^2 / r = (v_circ_scale^2 * M/L) / r.
    #
    # Let's implement:
    # a_N = (v_circ_scale ** 2 * mass_to_light_ratio) / safe_r
    # But units: v_circ_scale is km/s. r is kpc.
    # We need consistent units.
    # Let's work in km/s and kpc.
    # a_0 = 1.2e-10 m/s^2.
    # 1 km/s / 1 kpc = (1000 m/s) / (3.086e19 m) = 3.24e-17 s^-2.
    # a_0 in (km/s)^2 / kpc = 1.2e-10 * (1 kpc / 1000 m) * (1 km/s / 1000 m/s)^-2 ?
    # a_0 [km^2/s^2/kpc] = a_0 [m/s^2] * (1 kpc / 1000 m) * (1000 m / 1 km)^2 ?
    # 1 m/s^2 = 1 (m/s^2) * (1 km / 1000 m) / (1 s / 1 s)^2 * (1 kpc / 3.086e19 m) * 3.086e19 ?
    # Let's convert a_0 to (km/s)^2 / kpc.
    # a_0 = 1.2e-10 m/s^2.
    # 1 m = 1e-3 km. 1 kpc = 3.086e19 m = 3.086e16 km.
    # a_0 = 1.2e-10 * (1e-3 km) / s^2 = 1.2e-13 km/s^2.
    # a_0 (km/s^2/kpc) = 1.2e-13 km/s^2 / (3.086e16 km) = 3.89e-30 1/s^2? No.
    # Acceleration a has units [L]/[T]^2.
    # a_0 in km/s^2 = 1.2e-13 km/s^2.
    # To get (km/s)^2 / kpc:
    # (km/s)^2 / kpc = km^2 / (s^2 * kpc) = km / s^2 * (km/kpc).
    # a_0 [km/s^2] * (1 kpc / 3.086e16 km) ? No.
    # We want X such that X (km/s)^2 / kpc = 1.2e-10 m/s^2.
    # 1.2e-10 m/s^2 = 1.2e-13 km/s^2.
    # 1 (km/s)^2 / kpc = 1 km^2 / (s^2 * kpc) = 1 km / s^2 * (1 km / 1 kpc).
    # 1 km / 1 kpc = 1 / 3.086e16.
    # So 1 (km/s)^2 / kpc = (1/3.086e16) km/s^2.
    # Therefore, a_0 (in desired units) = 1.2e-13 km/s^2 / (1/3.086e16) (km/s)^2/kpc
    # = 1.2e-13 * 3.086e16 = 3.7032e3 (km/s)^2/kpc.
    # Let's verify: 3700 (km/s)^2 / 1 kpc = 3700 km^2/s^2/kpc = 3700 * (1/3.086e16) km/s^2 = 1.2e-13 km/s^2. Correct.
    # So A0_kpc = 3703.2 (km/s)^2 / kpc.

    A0_kpc = 3703.2  # (km/s)^2 / kpc

    # Newtonian acceleration in (km/s)^2 / kpc
    # a_N = (v_scale^2 * M/L) / r
    # where v_scale is in km/s, r in kpc.
    # v_scale is the velocity parameter passed to the function.
    # We treat `v_circ_scale` as the velocity scale of the baryonic mass.
    # So v_N^2 = (v_circ_scale ** 2) * mass_to_light_ratio
    # a_N = v_N^2 / r
    a_N = (v_circ_scale ** 2 * mass_to_light_ratio) / safe_r

    # MOND 'simple' interpolating function:
    # a = a_N / 2 + sqrt((a_N / 2)^2 + a_N * a_0)
    # This calculates the total acceleration a.
    # Then v_circ = sqrt(a * r)
    # v_circ^2 = a * r
    # v_circ^2 = r * (a_N/2 + sqrt((a_N/2)^2 + a_N*a_0))
    # Substitute a_N = v_N^2 / r:
    # v_circ^2 = r * ( (v_N^2/r)/2 + sqrt( ((v_N^2/r)/2)^2 + (v_N^2/r)*a_0 ) )
    # v_circ^2 = v_N^2/2 + sqrt( (v_N^2/2)^2 + v_N^2 * r * a_0 )
    # v_circ = sqrt( v_N^2/2 + sqrt( (v_N^2/2)^2 + v_N^2 * r * a_0 ) )
    # where v_N^2 = v_circ_scale^2 * M/L.

    v_N_squared = (v_circ_scale ** 2) * mass_to_light_ratio
    term1 = v_N_squared / 2.0
    term2 = np.sqrt((v_N_squared / 2.0) ** 2 + v_N_squared * r * A0_kpc)

    v_pred_squared = term1 + term2
    v_pred = np.sqrt(np.maximum(v_pred_squared, 0.0))

    return v_pred
