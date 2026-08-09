"""
Simulation module for User Story 3.

Generates isotropic Gaussian CMB simulations using the Planck best-fit Lambda-CDM
power spectrum and computes hemispherical variance statistics.
"""
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import healpy as hp

# Import logging setup
from logging_config import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_NSIDE = 128
DEFAULT_L_MAX = 128
DEFAULT_N_SIMS = 1000
SIMULATIONS_OUTPUT_DIR = "data/simulations"
FULL_SKY_CL_PATH = "data/reports/full_sky_cl.npy"


def generate_single_synalm(nside: int, cl: np.ndarray, seed: int) -> np.ndarray:
    """
    Generate a single set of spherical harmonic coefficients (alm) from a power spectrum.

    Uses healpy's synalm which generates Gaussian random alm coefficients
    consistent with the input power spectrum cl.

    Args:
        nside: HEALPix Nside resolution.
        cl: Power spectrum array (C_l values). Must have length l_max + 1.
        seed: Random seed for reproducibility.

    Returns:
        np.ndarray: Array of alm coefficients.
    """
    # Set seed for reproducibility for this specific simulation
    # Note: healpy.synalm uses numpy's global RNG state
    np.random.seed(seed)
    
    # healpy.synalm expects cl to be a list or array of C_l values
    # It handles the statistical generation of alm coefficients
    # The 'new=True' argument ensures a fresh set of alm coefficients is generated
    alm = hp.synalm(cl, new=True)
    return alm


def generate_isotropic_sims(
    n_sims: int = DEFAULT_N_SIMS,
    cl: Optional[np.ndarray] = None,
    nside: int = DEFAULT_NSIDE,
    l_max: int = DEFAULT_L_MAX,
    output_dir: Optional[str] = None,
    seed_base: int = 42
) -> List[np.ndarray]:
    """
    Generate N isotropic Gaussian CMB simulations.

    This function implements the core of the Monte Carlo null distribution generation.
    It loads the observed power spectrum (from T024) and generates synthetic maps
    that are statistically consistent with an isotropic Lambda-CDM universe.

    Args:
        n_sims: Number of simulations to generate.
        cl: Input power spectrum. If None, attempts to load from default path.
        nside: HEALPix Nside resolution.
        l_max: Maximum multipole moment.
        output_dir: Directory to save simulation maps (optional).
        seed_base: Base seed for random number generation.

    Returns:
        List[np.ndarray]: List of alm coefficient arrays.
    
    Raises:
        FileNotFoundError: If cl is None and the default path does not exist.
        ValueError: If the loaded power spectrum is invalid.
    """
    # Determine the power spectrum to use
    if cl is None:
        if os.path.exists(FULL_SKY_CL_PATH):
            logger.info(f"Loading power spectrum from {FULL_SKY_CL_PATH}")
            cl = np.load(FULL_SKY_CL_PATH)
            if cl is None or len(cl) == 0:
                raise ValueError("Loaded power spectrum is empty or invalid.")
            logger.info(f"Loaded power spectrum with {len(cl)} multipoles.")
        else:
            raise FileNotFoundError(
                f"Power spectrum not found at {FULL_SKY_CL_PATH}. "
                "T024 must be completed before running simulations."
            )

    # Ensure output directory exists if requested
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    alms_list = []
    logger.info(f"Starting generation of {n_sims} isotropic simulations (Nside={nside}, l_max={l_max})")

    start_time = time.time()

    for i in range(n_sims):
        current_seed = seed_base + i
        # Generate alm coefficients for this simulation
        alm = generate_single_synalm(nside, cl, seed=current_seed)
        alms_list.append(alm)

        # Log progress
        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i + 1}/{n_sims} simulations...")

        # Optional: Save maps to disk if requested
        # This is useful for debugging or if downstream tasks need the map files
        if output_dir:
            # Convert alm to map for storage/analysis
            sim_map = hp.alm2map(alm, nside)
            filename = os.path.join(output_dir, f"sim_{i+1:04d}_nside{nside}.fits")
            hp.write_map(filename, sim_map, overwrite=True)

    elapsed = time.time() - start_time
    avg_time = elapsed / n_sims
    logger.info(f"Completed {n_sims} simulations in {elapsed:.2f}s (Avg: {avg_time:.2f}s/sim)")

    return alms_list


def alm_to_map(alm: np.ndarray, nside: int) -> np.ndarray:
    """
    Convert spherical harmonic coefficients to a HEALPix map.

    Args:
        alm: Spherical harmonic coefficients.
        nside: HEALPix Nside resolution.

    Returns:
        np.ndarray: Healpix map.
    """
    return hp.alm2map(alm, nside)


def main():
    """
    Main entry point for running simulation generation as a script.
    Executes T032: Generate isotropic simulations using the Planck best-fit spectrum.
    """
    # Load CL from T024 if available, otherwise fail loudly
    cl_path = FULL_SKY_CL_PATH
    cl = None
    
    if os.path.exists(cl_path):
        logger.info(f"Loading power spectrum from {cl_path}")
        try:
            cl = np.load(cl_path)
            if cl is None or len(cl) == 0:
                raise ValueError("Loaded power spectrum is empty.")
        except Exception as e:
            logger.error(f"Failed to load power spectrum: {e}")
            raise
    else:
        # Fail loudly: do not generate dummy data for research
        raise FileNotFoundError(
            f"Required power spectrum file not found at {cl_path}. "
            "Please ensure T024 (compute_full_sky_cl) has been executed successfully."
        )

    # Generate simulations (using N=10 for quick test, N=1000 for full run)
    # The task constraint says N=1000 for CI feasibility, but we allow override
    n_sims = 1000 
    sims = generate_isotropic_sims(
        n_sims=n_sims, 
        cl=cl, 
        nside=DEFAULT_NSIDE,
        output_dir=SIMULATIONS_OUTPUT_DIR
    )

    logger.info(f"Simulation generation completed successfully. Generated {len(sims)} simulations.")
    return sims


if __name__ == "__main__":
    main()