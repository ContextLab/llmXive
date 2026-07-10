"""
Monte Carlo simulation generation for isotropic null hypothesis.

Generates weighted event sets based on exact exposure maps.
"""
import numpy as np
import healpy as hp
from typing import List, Tuple

def generate_isotropic_events(
    n_events: int,
    exposure_map: np.ndarray,
    nside: int = 64,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic isotropic events weighted by exposure map.

    Args:
        n_events: Number of events to generate
        exposure_map: Expected exposure per pixel
        nside: HEALPix Nside
        seed: Random seed for reproducibility

    Returns:
        Tuple of (ra_deg, dec_deg) for generated events
    """
    if seed is not None:
        np.random.seed(seed)

    # Normalize exposure to get probability distribution
    pix_probs = exposure_map / np.sum(exposure_map)

    # Sample pixels based on exposure weights
    n_pix = hp.nside2npix(nside)
    sampled_pixels = np.random.choice(n_pix, size=n_events, p=pix_probs)

    # Convert pixels to random (theta, phi) within the pixel
    theta = np.zeros(n_events)
    phi = np.zeros(n_events)

    for i, pix in enumerate(sampled_pixels):
        # Get pixel center and area for random sampling
        # Simple approximation: sample uniformly within pixel bounds
        # For rigorous work, use exact pixel geometry integration
        pix_centers = hp.pix2ang(nside, pix)
        # Add small random offset within pixel (simplified)
        # Real implementation should integrate over pixel area
        theta[i] = pix_centers[0] + (np.random.rand() - 0.5) * hp.nside2resol(nside)
        phi[i] = pix_centers[1] + (np.random.rand() - 0.5) * hp.nside2resol(nside)

    # Convert to RA/Dec
    dec_rad = np.pi / 2.0 - theta
    ra_rad = phi % (2 * np.pi)

    dec_deg = np.degrees(dec_rad)
    ra_deg = np.degrees(ra_rad)

    return ra_deg, dec_deg
