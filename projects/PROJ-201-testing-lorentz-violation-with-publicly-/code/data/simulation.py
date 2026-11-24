"""
Simulation utilities for CMB anisotropy studies.

This module provides functions to generate isotropic Gaussian CMB
realizations, construct Lorentz‑violation modulation fields, inject
the SME coefficient into spherical harmonic coefficients, and produce
a final sky map suitable for downstream analysis.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import healpy as hp
import numpy as np

from code.config import load_config
from code.utils.logging import setup_logger

logger = setup_logger(__name__)

def load_config_for_simulation(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration specific to simulations.

    Parameters
    ----------
    config_path : str, optional
        Path to a YAML configuration file. If None, the default
        ``config.yaml`` in the current working directory is used.

    Returns
    ----------
    dict
        Dictionary containing the ``simulation`` section of the
        configuration (or an empty dict if not present).
    """
    config = load_config(Path(config_path) if config_path else None)
    return config.get("simulation", {})

def generate_isotropic_alm(
    nside: int,
    l_max: int,
    cl_tt: np.ndarray,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Generate isotropic Gaussian random spherical harmonic coefficients.

    Parameters
    ----------
    nside : int
        HEALPix Nside of the target map.
    l_max : int
        Maximum multipole moment to generate.
    cl_tt : np.ndarray
        The temperature angular power spectrum (C_ℓ) up to ``l_max``.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    ----------
    np.ndarray
        Array of ``a_ℓm`` coefficients in HEALPix ordering.
    """
    if seed is not None:
        np.random.seed(seed)
    logger.info(
        f"Generating isotropic alm: nside={nside}, l_max={l_max}, seed={seed}"
    )
    # healpy.synalm expects the full set of spectra; we provide only TT.
    # The function returns a complex array of alm coefficients.
    alm = hp.synalm(cl_tt, lmax=l_max, new=True)
    return alm

def construct_alpha_lm(
    nside: int,
    l_max: int,
    k: float,
    alpha_lm_iso: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Construct the modulation field coefficients (α_ℓm) representing
    Lorentz‑violation anisotropy.

    The modulation field is modeled as a Gaussian random field
    scaled by the SME coefficient ``k``.  If ``alpha_lm_iso`` is
    provided it is used as a deterministic template; otherwise a
    random realization is generated.

    Parameters
    ----------
    nside : int
        HEALPix Nside.
    l_max : int
        Maximum multipole.
    k : float
        SME coefficient scaling factor.
    alpha_lm_iso : np.ndarray, optional
        Optional deterministic template for the modulation field.
    seed : int, optional
        Random seed.

    Returns
    ----------
    np.ndarray
        Array of α_ℓm coefficients.
    """
    if seed is not None:
        np.random.seed(seed)
    if alpha_lm_iso is not None:
        logger.info("Using provided isotropic alpha_lm template.")
        return k * alpha_lm_iso

    # Simple placeholder: generate a random Gaussian field with unit variance
    # and scale by the coefficient k.
    logger.info(
        f"Constructing random alpha_lm: nside={nside}, l_max={l_max}, k={k}"
    )
    # For a unit‑variance field we can reuse synalm with a flat spectrum.
    cl_flat = np.ones(l_max + 1)
    alpha_lm = hp.synalm(cl_flat, lmax=l_max, new=True)
    return k * alpha_lm

def inject_sme_coefficient(
    isotropic_alm: np.ndarray,
    alpha_lm: np.ndarray,
    k: float,
) -> np.ndarray:
    """
    Inject the SME coefficient into isotropic spherical harmonic coefficients.

    The forward‑model injection follows:
    ``a_ℓm^{new} = a_ℓm^{iso} + k * α_ℓm``

    Parameters
    ----------
    isotropic_alm : np.ndarray
        Isotropic ``a_ℓm`` coefficients.
    alpha_lm : np.ndarray
        Modulation field coefficients (α_ℓm).
    k : float
        SME coefficient (e.g., ``k_{(V)00}^{(5)}``).

    Returns
    ----------
    np.ndarray
        New ``a_ℓm`` array with the Lorentz‑violating contribution added.
    """
    logger.info(
        f"Injecting SME coefficient k={k} into isotropic alm (size={isotropic_alm.size})"
    )
    if isotropic_alm.shape != alpha_lm.shape:
        raise ValueError(
            f"Shape mismatch: isotropic_alm {isotropic_alm.shape} vs alpha_lm {alpha_lm.shape}"
        )
    return isotropic_alm + k * alpha_lm

def simulate_cmb_map(
    nside: int,
    l_max: int,
    cl_tt: np.ndarray,
    k: float,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Produce a simulated CMB map with an injected SME coefficient.

    This convenience wrapper generates an isotropic realization,
    constructs the modulation field, injects the coefficient, and
    converts the resulting ``a_ℓm`` back to a HEALPix map.

    Parameters
    ----------
    nside : int
        Desired HEALPix Nside of the output map.
    l_max : int
        Maximum multipole to include.
    cl_tt : np.ndarray
        Temperature power spectrum.
    k : float
        SME coefficient to inject.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    ----------
    np.ndarray
        Processed sky map (1‑D array of pixel values).
    """
    logger.info(
        f"Simulating CMB map with nside={nside}, l_max={l_max}, k={k}, seed={seed}"
    )
    # 1. Generate isotropic alm
    isotropic_alm = generate_isotropic_alm(nside, l_max, cl_tt, seed=seed)

    # 2. Construct modulation field (α_ℓm)
    alpha_lm = construct_alpha_lm(nside, l_max, k, seed=seed)

    # 3. Inject SME coefficient
    injected_alm = inject_sme_coefficient(isotropic_alm, alpha_lm, k)

    # 4. Convert back to map
    simulated_map = hp.alm2map(injected_alm, nside, pixwin=False)

    logger.info("Simulation complete.")
    return simulated_map

# The module deliberately does not execute any code on import; it provides
# reusable functions for the rest of the pipeline.