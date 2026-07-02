"""
Module for generating simulated CMB maps using CAMB.
"""
import os
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import healpy as hp

from code.config import N_SIDE, COSMO_PARAMS, BASE_SEED, DATA_DERIVED_DIR, DATA_METADATA_DIR
from code.data_io import save_map_to_fits, save_metadata

logger = logging.getLogger(__name__)

def get_camb_version() -> str:
    """Get CAMB version string."""
    try:
        import camb
        return camb.__version__
    except ImportError:
        return "unknown"

def generate_cmb_map(
    seed: int,
    nside: int = N_SIDE,
    params: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """
    Generate a CMB temperature map using CAMB.

    Args:
        seed: Random seed for realization.
        nside: HEALPix Nside.
        params: Cosmological parameters.

    Returns:
        1D array of temperature map.
    """
    import camb
    from camb import model, initialpower

    if params is None:
        params = COSMO_PARAMS

    # Set CAMB parameters
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=params["H0"], ombh2=0.022, omch2=0.12)
    pars.InitPower.set_params(As=2.1e-9, ns=params["n_s"], r=0.0)
    # Note: tau is ignored for T-only in this simple setup

    # Get power spectrum
    results = camb.get_results(pars)
    cl = results.get_cmb_power_spectra(pars, lmax=3*nside)
    # cl is a list of arrays: T, E, B, TE, TB, EB
    # We only need T (index 0)
    cl_t = cl[:, 0]  # Shape (l_max+1,)

    # Generate map
    np.random.seed(seed)
    map_data = hp.synfast(cl_t, nside=nside, new=True)
    return map_data

def compute_checksum(data: np.ndarray) -> str:
    """Compute checksum of data."""
    return hashlib.sha256(data.tobytes()).hexdigest()

def save_map_to_fits_wrapper(
    map_data: np.ndarray,
    output_path: Path,
    metadata: Dict[str, Any],
) -> str:
    """Wrapper for data_io save function."""
    return save_map_to_fits(map_data, output_path, metadata)

def save_metadata_wrapper(
    metadata: Dict[str, Any],
    output_path: Path,
) -> None:
    """Wrapper for data_io save metadata."""
    save_metadata(metadata, output_path)

def load_existing_map(path: Path) -> np.ndarray:
    """Load existing map if present."""
    import healpy as hp
    return hp.read_map(path)

def load_existing_mask(path: Path) -> np.ndarray:
    """Load existing mask if present."""
    import healpy as hp
    return hp.read_map(path)

def main():
    """Main entry point for map generation."""
    logger.info("Starting CMB map generation...")
    # Example usage
    seed = 42
    map_data = generate_cmb_map(seed)
    logger.info(f"Generated map with seed {seed}, size {len(map_data)}")

if __name__ == "__main__":
    main()
