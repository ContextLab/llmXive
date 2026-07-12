"""
Simulation module for generating CMB maps with Lorentz violation signatures.

This module handles the generation of isotropic CMB maps, the construction of
anisotropic modulation fields (alpha_lm), and the injection of Standard Model
Extension (SME) coefficients into the spherical harmonic coefficients (a_lm).
"""

import numpy as np
import healpy as hp
from typing import Tuple, Optional, List, Dict, Any
import logging
from pathlib import Path

from code.utils.logging import setup_logger
from code.config import load_config

# Initialize logger for this module
logger = setup_logger(__name__)


def load_config_for_simulation(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration specifically for simulation parameters.

    Args:
        config_path: Optional path to config.yaml. If None, uses default location.

    Returns:
        Dictionary containing simulation configuration.
    """
    return load_config(config_path)


def generate_isotropic_alm(
    nside: int,
    l_max: int,
    cl_tt: np.ndarray,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate isotropic Gaussian random spherical harmonic coefficients (a_lm).

    Args:
        nside: HEALPix Nside parameter.
        l_max: Maximum multipole moment to generate.
        cl_tt: Angular power spectrum C_l for TT mode.
        seed: Random seed for reproducibility.

    Returns:
        Array of a_lm coefficients in HEALPix ordering.
    """
    if seed is not None:
        np.random.seed(seed)

    # Use healpy's synalm to generate a_lm from power spectrum
    # synalm expects Cl array indexed by l, with shape (ncomp, l_max+1)
    # For TT only, we pass a 2D array with shape (1, l_max+1)
    cl_array = cl_tt.reshape(1, -1)
    alm = hp.synalm(cl_array, l_max=l_max, new=True)
    return alm


def construct_alpha_lm(
    nside: int,
    l_max: int,
    k: float,
    alpha_lm_iso: Optional[np.ndarray] = None,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Construct the modulation field coefficients (alpha_lm) representing
    Lorentz violation anisotropy.

    The modulation field alpha(l,m) is modeled as a stochastic field
    scaled by the SME coefficient k.

    Args:
        nside: HEALPix Nside parameter.
        l_max: Maximum multipole moment.
        k: SME coefficient scaling factor (e.g., k_(V)00^(5)).
        alpha_lm_iso: Optional isotropic background for alpha_lm.
        seed: Random seed for reproducibility.

    Returns:
        Array of alpha_lm coefficients.
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate a random Gaussian field for the modulation
    # We simulate alpha_lm as a random field with a specific power spectrum
    # For simplicity in this skeleton, we use a flat spectrum scaled by k
    # In a full implementation, this would use a theoretical C_l^alpha
    cl_alpha = np.ones(l_max + 1) * (k ** 2) * 1e-6  # Placeholder spectrum
    cl_alpha[0] = 0  # No monopole

    if alpha_lm_iso is not None:
        # Add to existing field
        alpha_lm = alpha_lm_iso + hp.synalm(cl_alpha.reshape(1, -1), l_max=l_max, new=True)
    else:
        alpha_lm = hp.synalm(cl_alpha.reshape(1, -1), l_max=l_max, new=True)

    return alpha_lm


def inject_sme_coefficient(
    a_lm_iso: np.ndarray,
    alpha_lm: np.ndarray,
    k: float
) -> np.ndarray:
    """
    Inject the SME coefficient into the isotropic spherical harmonic coefficients.

    This implements the forward model:
        a_lm_new = a_lm_iso + k * alpha_lm

    Where:
        a_lm_iso: Isotropic spherical harmonic coefficients.
        alpha_lm: Modulation field coefficients representing anisotropy.
        k: The SME coefficient (scalar scaling factor).

    The injection occurs BEFORE convolution with beam functions.

    Args:
        a_lm_iso: Input isotropic a_lm coefficients (HEALPix ordering).
        alpha_lm: Modulation field coefficients.
        k: SME coefficient value to inject.

    Returns:
        Modified a_lm coefficients with injected Lorentz violation.

    Raises:
        ValueError: If input arrays have incompatible shapes or k is invalid.
    """
    if not isinstance(k, (int, float)):
        raise ValueError(f"SME coefficient k must be a number, got {type(k)}")

    if a_lm_iso.shape != alpha_lm.shape:
        raise ValueError(
            f"Shape mismatch: a_lm_iso {a_lm_iso.shape} != alpha_lm {alpha_lm.shape}"
        )

    if np.isnan(k) or np.isinf(k):
        raise ValueError(f"SME coefficient k must be finite, got {k}")

    logger.debug(f"Injecting SME coefficient k={k} into {len(a_lm_iso)} modes")

    # Perform the injection: a_lm_new = a_lm_iso + k * alpha_lm
    a_lm_new = a_lm_iso + k * alpha_lm

    return a_lm_new


def simulate_cmb_map(
    a_lm: np.ndarray,
    nside: int,
    pixel_noise_sigma: float = 0.0,
    beam_fwhm_arcmin: float = 0.0
) -> np.ndarray:
    """
    Convert spherical harmonic coefficients to a HEALPix map.

    Args:
        a_lm: Spherical harmonic coefficients.
        nside: HEALPix Nside parameter.
        pixel_noise_sigma: Gaussian noise standard deviation per pixel.
        beam_fwhm_arcmin: Beam FWHM in arcminutes (0 for no beam).

    Returns:
        HEALPix map (1D array of pixel values).
    """
    # Convert alm to map
    if beam_fwhm_arcmin > 0:
        # Apply beam smoothing
        alm_smooth = hp.smoothing(a_lm, fwhm=np.radians(beam_fwhm_arcmin / 60.0))
        map_out = hp.alm2map(alm_smooth, nside)
    else:
        map_out = hp.alm2map(a_lm, nside)

    # Add noise if requested
    if pixel_noise_sigma > 0:
        np.random.seed(int(np.sum(map_out) * 1000) % 2**32) # Deterministic-ish seed from map
        noise = np.random.normal(0, pixel_noise_sigma, size=map_out.shape)
        map_out += noise

    return map_out