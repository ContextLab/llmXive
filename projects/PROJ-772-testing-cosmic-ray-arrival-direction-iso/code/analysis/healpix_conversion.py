"""
HEALPix conversion utilities.

Converts RA/Dec coordinates to HEALPix pixel indices (Nside=64).
"""
import numpy as np
import healpy as hp

def ra_dec_to_healpix(ra_deg: np.ndarray, dec_deg: np.ndarray, nside: int = 64) -> np.ndarray:
    """
    Convert Right Ascension and Declination to HEALPix pixel indices.

    Args:
        ra_deg: Array of RA in degrees [0, 360)
        dec_deg: Array of Dec in degrees [-90, 90]
        nside: HEALPix Nside parameter (default 64)

    Returns:
        Array of pixel indices
    """
    # Convert to radians
    ra_rad = np.radians(ra_deg)
    dec_rad = np.radians(dec_deg)

    # Convert to theta (colatitude) and phi (longitude)
    # theta = pi/2 - dec, phi = ra
    theta = np.pi / 2.0 - dec_rad
    phi = ra_rad

    # Handle wrap-around for phi
    phi = np.mod(phi, 2 * np.pi)

    # Convert to HEALPix indices
    # Check for valid range
    valid_mask = (dec_deg >= -90) & (dec_deg <= 90)
    indices = np.full_like(ra_deg, -1, dtype=int)
    indices[valid_mask] = hp.ang2pix(nside, theta[valid_mask], phi[valid_mask])

    return indices
