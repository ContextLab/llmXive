"""
Exposure correction utilities.

Generates exposure-corrected intensity maps.
"""
import numpy as np
import healpy as hp

def correct_for_exposure(
    observed_map: np.ndarray,
    exposure_map: np.ndarray,
    nside: int = 64
) -> np.ndarray:
    """
    Correct observed counts map by dividing by expected exposure.

    Args:
        observed_map: Observed event counts per pixel
        exposure_map: Expected exposure per pixel (from detector footprint)
        nside: HEALPix Nside

    Returns:
        Exposure-corrected intensity map (I = N_obs / N_exp)
    """
    # Avoid division by zero
    epsilon = 1e-10
    corrected = np.zeros_like(observed_map, dtype=float)

    valid_mask = exposure_map > epsilon
    corrected[valid_mask] = observed_map[valid_mask] / exposure_map[valid_mask]

    return corrected
