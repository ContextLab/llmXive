"""
Angular power spectrum computation.

Computes spherical-harmonic coefficients and C_l values with shot-noise subtraction.
"""
import numpy as np
import healpy as hp

def compute_cl_from_map(
    healpix_map: np.ndarray,
    nside: int = 64,
    l_max: int = 5,
    shot_noise: bool = True,
    n_tot: Optional[float] = None
) -> Dict[str, np.ndarray]:
    """
    Compute angular power spectrum C_l from a HEALPix map.

    Args:
        healpix_map: Map values (intensity or counts)
        nside: HEALPix Nside
        l_max: Maximum ell to compute
        shot_noise: If True, subtract 1/N_tot
        n_tot: Total number of events (for shot noise)

    Returns:
        Dict with 'ell', 'cl', and 'cl_err'
    """
    # Convert map to alm
    alm = hp.map2alm(healpix_map, lmax=l_max, pol=False)

    # Compute Cl
    cl = hp.alm2cl(alm)

    # Shot noise subtraction
    if shot_noise and n_tot is not None and n_tot > 0:
        # Shot noise level is 1/N_tot for Poisson statistics
        noise_level = 1.0 / n_tot
        cl = np.maximum(cl - noise_level, 0.0)

    ell = np.arange(len(cl))

    return {
        "ell": ell,
        "cl": cl,
        "cl_err": np.sqrt(2.0 / (2 * ell + 1)) * cl  # Simple Gaussian error approx
    }
