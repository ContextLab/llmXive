"""
Simulation module for generating CMB maps with Lorentz violation injection.

This module implements the forward model for injecting Standard Model Extension (SME)
coefficients into isotropic CMB maps to test for Lorentz violation signatures.

Forward Model Algorithm
======================

The core injection logic modifies the spherical harmonic coefficients (a_lm) of an
isotropic CMB map before any beam convolution or noise addition occurs. This ensures
the Lorentz-violating signal is imprinted at the theoretical level of the sky realization.

Algorithm Steps:
1. Generate or load an isotropic Gaussian random field in a_lm space (a_lm_iso).
   - The power spectrum C_l is derived from the standard Lambda-CDM model.
   - Real and imaginary parts are drawn from N(0, C_l/2).

2. Construct the Lorentz-violating perturbation mode (alpha_lm).
   - This mode represents the specific angular dependence of the SME coefficient
     k_(V)00^(5). For the dipole/quadrupole violation scenario, alpha_lm is
     constructed from specific spherical harmonic basis functions Y_lm corresponding
     to the violation multipole.

3. Apply the injection formula:
   a_lm_new = a_lm_iso + k * alpha_lm

   Where:
   - a_lm_new: The modified spherical harmonic coefficients containing the LV signal.
   - a_lm_iso: The original isotropic coefficients.
   - k: The magnitude of the SME coefficient (k_(V)00^(5)). This is a scalar parameter
       constrained by the physics model.
   - alpha_lm: The shape/function of the violation in harmonic space.

   CRITICAL: This operation MUST happen BEFORE convolution with beam functions.
   If beam convolution (B_l) is applied later, the observed coefficients become:
   a_lm_obs = B_l * a_lm_new = B_l * (a_lm_iso + k * alpha_lm)
   If injection happened after convolution, the physics would be incorrect:
   a_lm_obs_wrong = B_l * a_lm_iso + k * alpha_lm  (Incorrect: k term not suppressed by beam)

4. Transform a_lm_new back to pixel space (Healpix map) via hp.alm2map.

5. Convolve with instrumental beam B_l and add noise N_l (if simulating observations).
   - This step happens AFTER the injection to model realistic telescope data.

6. Write the resulting map to a FITS file.

Note on SME Coefficient k_(V)00^(5):
This specific coefficient corresponds to a dimension-5 operator in the photon sector
of the SME, leading to a frequency-dependent rotation of polarization and potential
anisotropy in the temperature power spectrum.

References:
- Kostelecky, V. A., & Mewes, M. (2008). Signals for Lorentz violation in electrodynamics.
- Planck Collaboration (2020). Planck 2018 results. VII. Isotropy and Statistics of the CMB.
"""

import numpy as np
import healpy as hp
from typing import Tuple, Optional, List, Dict, Any
import logging

from code.utils.logging import setup_logger
from code.config import load_config

logger = setup_logger(__name__)


def generate_isotropic_alm(
    l_max: int,
    cl: np.ndarray,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate isotropic Gaussian random spherical harmonic coefficients.

    Parameters
    ----------
    l_max : int
        Maximum multipole moment l.
    cl : np.ndarray
        Power spectrum C_l for l=0 to l_max.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    np.ndarray
        Array of alm coefficients in standard Healpix ordering.
    """
    if seed is not None:
        np.random.seed(seed)

    n_alm = hp.Alm.getsize(l_max)
    alm = np.zeros(n_alm, dtype=np.complex128)

    # Generate real and imaginary parts
    # For m=0, coefficients are real. For m>0, real and imag are independent N(0, C_l/2).
    idx = 0
    for l in range(l_max + 1):
        c_l = cl[l]
        if c_l <= 0:
            # Skip if power is zero or negative (numerical issues)
            idx += l + 1
            continue

        var = c_l / 2.0

        # m=0 term (real)
        alm[idx] = np.random.normal(0, np.sqrt(var))
        idx += 1

        # m=1 to l terms (complex)
        for m in range(1, l + 1):
            re = np.random.normal(0, np.sqrt(var))
            im = np.random.normal(0, np.sqrt(var))
            alm[idx] = re + 1j * im
            idx += 1

    return alm


def construct_alpha_lm(
    l_max: int,
    multipole: int = 2,
    phase: float = 0.0
) -> np.ndarray:
    """
    Construct the alpha_lm perturbation mode for Lorentz violation.

    This function generates the specific harmonic structure alpha_lm associated
    with the SME coefficient k_(V)00^(5). For the purpose of this forward model,
    we assume a dipole-like or quadrupole-like modulation depending on the
    specified multipole.

    The alpha_lm is normalized such that its power spectrum sums to 1, allowing
    the scalar k to control the overall amplitude of the violation.

    Parameters
    ----------
    l_max : int
        Maximum multipole moment.
    multipole : int
        The multipole order of the violation (e.g., 1 for dipole, 2 for quadrupole).
    phase : float
        Phase angle for the orientation of the violation axis.

    Returns
    -------
    np.ndarray
        Alpha_lm coefficients in Healpix ordering.
    """
    logger.info(f"Constructing alpha_lm for multipole={multipole}, phase={phase:.2f}")

    # Initialize zeros
    n_alm = hp.Alm.getsize(l_max)
    alpha = np.zeros(n_alm, dtype=np.complex128)

    # For a simple model, we inject power at the specific multipole l = multipole
    # and distribute it according to spherical harmonic properties.
    # In a full physical model, this would be derived from the specific SME operator.
    # Here we implement a simplified "preferred direction" model.

    l_target = multipole
    if l_target > l_max:
        logger.warning(f"Requested multipole {l_target} > l_max {l_max}. Setting l_target = l_max.")
        l_target = l_max

    # Set coefficients for l = l_target
    # We assume a specific m-mode (e.g., m=0 for axisymmetric, or random phase)
    # For this implementation, we use a simple pattern that breaks isotropy.
    # A common choice for testing is a pure m=0 mode at the target l.

    idx = hp.Alm.getidx(l_target, 0)
    # Real amplitude for m=0
    alpha[idx] = 1.0 + 0j

    # If we want a more complex pattern, we could add other m modes here.
    # For now, this simple injection is sufficient to test the pipeline's
    # ability to detect a non-zero k.

    logger.info(f"Alpha_lm constructed with non-zero entry at l={l_target}, m=0")
    return alpha


def inject_sme_coefficient(
    alm_iso: np.ndarray,
    k: float,
    alpha_lm: np.ndarray
) -> np.ndarray:
    """
    Inject the SME coefficient into isotropic alm coefficients.

    This function implements the core forward model equation:
        a_lm_new = a_lm_iso + k * alpha_lm

    This operation is performed BEFORE any beam convolution or noise addition.

    Parameters
    ----------
    alm_iso : np.ndarray
        Isotropic spherical harmonic coefficients.
    k : float
        The SME coefficient magnitude (k_(V)00^(5)).
    alpha_lm : np.ndarray
        The perturbation mode structure.

    Returns
    -------
    np.ndarray
        Modified spherical harmonic coefficients.
    """
    if alm_iso.shape != alpha_lm.shape:
        raise ValueError(f"Shape mismatch: alm_iso {alm_iso.shape} vs alpha_lm {alpha_lm.shape}")

    logger.debug(f"Injecting SME coefficient k={k}")
    alm_new = alm_iso + k * alpha_lm
    return alm_new


def simulate_cmb_map(
    l_max: int,
    cl_iso: np.ndarray,
    k: float,
    alpha_lm: Optional[np.ndarray] = None,
    beam_fwhm_arcmin: float = 5.0,
    noise_sigma: float = 1e-5,
    seed: Optional[int] = None,
    nside: int = 256
) -> np.ndarray:
    """
    Generate a simulated CMB map with Lorentz violation injection.

    Full pipeline:
    1. Generate isotropic alm.
    2. Construct alpha_lm if not provided.
    3. Inject SME coefficient (a_lm_new = a_lm_iso + k * alpha_lm).
    4. Convert to map.
    5. Apply beam convolution.
    6. Add noise.

    Parameters
    ----------
    l_max : int
        Maximum multipole.
    cl_iso : np.ndarray
        Isotropic power spectrum.
    k : float
        SME coefficient magnitude.
    alpha_lm : np.ndarray, optional
        Pre-computed alpha_lm. If None, generated internally.
    beam_fwhm_arcmin : float
        Beam FWHM in arcminutes.
    noise_sigma : float
        Pixel noise standard deviation.
    seed : int, optional
        Random seed.
    nside : int
        Healpix Nside resolution.

    Returns
    -------
    np.ndarray
        Simulated CMB map in pixel space.
    """
    if seed is not None:
        np.random.seed(seed)

    # Step 1: Generate isotropic alm
    alm_iso = generate_isotropic_alm(l_max, cl_iso, seed=seed)

    # Step 2: Construct alpha_lm if needed
    if alpha_lm is None:
        alpha_lm = construct_alpha_lm(l_max, multipole=2, phase=0.0)

    # Step 3: Inject SME coefficient (CORE LOGIC)
    alm_new = inject_sme_coefficient(alm_iso, k, alpha_lm)

    # Step 4: Transform to map
    # Use smooth=False to get the raw map before beam convolution
    map_raw = hp.alm2map(alm_new, nside, lmax=l_max)

    # Step 5: Apply beam convolution
    # Healpy beam window function
    l = np.arange(l_max + 1)
    b_l = np.exp(-0.5 * (l * (l + 1)) * (np.radians(beam_fwhm_arcmin / 60.0) ** 2))
    # Apply beam in harmonic space would be more accurate, but for this demo
    # we can convolve the map or apply the window to the alm again.
    # Let's do it properly in alm space for accuracy.
    alm_new_beamed = np.zeros_like(alm_new)
    for l_val in range(l_max + 1):
        idx_start = hp.Alm.getidx(l_val, 0)
        idx_end = idx_start + l_val + 1
        alm_new_beamed[idx_start:idx_end] = alm_new[idx_start:idx_end] * b_l[l_val]

    map_beamed = hp.alm2map(alm_new_beamed, nside, lmax=l_max)

    # Step 6: Add noise
    n_pix = hp.nside2npix(nside)
    noise = np.random.normal(0, noise_sigma, n_pix)
    map_final = map_beamed + noise

    logger.info(f"Simulated map generated: Nside={nside}, k={k}, noise={noise_sigma}")
    return map_final


def load_config_for_simulation() -> Dict[str, Any]:
    """
    Load configuration specific to simulation parameters.

    Returns
    -------
    Dict[str, Any]
        Configuration dictionary.
    """
    config = load_config()
    return {
        'l_max': config.get('constants', {}).get('l_max', 200),
        'k_sme': config.get('constants', {}).get('sme_coefficient', 0.0),
        'nside': 256, # Default for simulation as per task T018
        'beam_fwhm': 5.0,
        'noise_sigma': 1e-5
    }