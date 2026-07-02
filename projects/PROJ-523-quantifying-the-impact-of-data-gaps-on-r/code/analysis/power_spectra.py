"""
Power Spectrum Analysis Module for CMB Gap Bias Analysis.

This module computes angular power spectra (C_l) from reconstructed CMB maps
using HEALPix's anafast function. It handles masked maps, applies window
functions if necessary, and outputs results in a structured format compatible
with the project's data schemas.

Dependencies:
    - healpy (>=1.15.0)
    - numpy
    - code.data_io (for I/O operations)
    - code.config (for global constants)
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import healpy as hp

# Import project constants and I/O utilities
from code.config import N_SIDE, DATA_DERIVED_DIR, DATA_RESULTS_DIR, DATA_METADATA_DIR
from code.data_io import load_map_from_fits, load_mask_from_fits, save_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_power_spectrum(
    map_data: np.ndarray,
    mask: Optional[np.ndarray] = None,
    lmax: int = 2000,
    use_pixel_weights: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the angular power spectrum (C_l) of a HEALPix map.

    Args:
        map_data: The HEALPix map data (temperature or polarization).
        mask: Optional mask array (0 for masked pixels, 1 for unmasked).
        lmax: Maximum multipole moment to compute (default: 2000).
        use_pixel_weights: If True, use pixel weights for map-based power spectrum estimation.

    Returns:
        Tuple of (l_values, Cl_values) where:
            - l_values: Array of multipole moments
            - Cl_values: Array of power spectrum values

    Raises:
        ValueError: If input map is invalid or contains NaNs after masking.
    """
    if map_data is None or not isinstance(map_data, np.ndarray):
        raise ValueError("map_data must be a valid numpy array.")

    if np.any(np.isnan(map_data)):
        logger.warning("Input map contains NaN values. Attempting to handle via mask...")
        if mask is None:
            # Create a mask that excludes NaN pixels
            mask = ~np.isnan(map_data)
            mask = mask.astype(float)
            logger.info(f"Created mask to exclude {np.sum(~mask)} NaN pixels.")
        else:
            # Apply existing mask and check for remaining NaNs
            masked_map = map_data * mask
            if np.any(np.isnan(masked_map)):
                raise ValueError("Map contains NaN values that could not be masked.")

    if mask is not None:
        if mask.shape != map_data.shape:
            raise ValueError("Mask shape must match map shape.")
        if not np.issubdtype(mask.dtype, np.floating) and not np.issubdtype(mask.dtype, np.integer):
            mask = mask.astype(float)

    logger.info(f"Computing power spectrum with lmax={lmax}, use_pixel_weights={use_pixel_weights}")
    
    # Healpy anafast parameters
    kwargs = {
        'lmax': lmax,
        'use_pixel_weights': use_pixel_weights,
        'pol': False  # Assuming temperature-only for now; extend if needed
    }

    if mask is not None:
        kwargs['map'] = map_data
        kwargs['mask'] = mask
        cl = hp.anafast(**kwargs)
    else:
        cl = hp.anafast(map_data, **kwargs)

    # Generate corresponding l values
    l_values = np.arange(len(cl))

    # Ensure no NaNs in output
    if np.any(np.isnan(cl)):
        logger.error("Power spectrum calculation resulted in NaN values.")
        # Replace NaNs with 0 or handle appropriately
        cl = np.nan_to_num(cl, nan=0.0)

    return l_values, cl


def save_power_spectrum_metadata(
    realization_id: str,
    algo_name: str,
    l_values: np.ndarray,
    cl_values: np.ndarray,
    metadata: Dict[str, Any]
) -> str:
    """
    Save power spectrum results and metadata to disk.

    Args:
        realization_id: Unique identifier for the realization.
        algo_name: Name of the gap-filling algorithm used.
        l_values: Array of multipole moments.
        cl_values: Array of power spectrum values.
        metadata: Dictionary containing additional metadata (e.g., execution time, parameters).

    Returns:
        Path to the saved metadata file.
    """
    # Ensure output directories exist
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_METADATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save power spectrum data
    cl_file_path = DATA_RESULTS_DIR / f"cl_{realization_id}_{algo_name}.npz"
    np.savez(cl_file_path, l=l_values, cl=cl_values)
    logger.info(f"Saved power spectrum data to {cl_file_path}")

    # Prepare metadata for saving
    meta_data = {
        "realization_id": realization_id,
        "algo_name": algo_name,
        "lmax": len(cl_values) - 1,
        "nside": N_SIDE,
        "computed_at": datetime.utcnow().isoformat(),
        "cl_file": str(cl_file_path),
        "summary_stats": {
            "mean_cl": float(np.mean(cl_values)),
            "std_cl": float(np.std(cl_values)),
            "min_cl": float(np.min(cl_values)),
            "max_cl": float(np.max(cl_values))
        }
    }
    meta_data.update(metadata)

    # Save metadata JSON
    meta_file_path = DATA_METADATA_DIR / f"cl_meta_{realization_id}_{algo_name}.json"
    save_metadata(meta_file_path, meta_data)
    logger.info(f"Saved power spectrum metadata to {meta_file_path}")

    return str(meta_file_path)


def process_realization_power_spectrum(
    realization_id: str,
    map_file: Path,
    mask_file: Optional[Path] = None,
    algo_name: str = "original",
    lmax: int = 2000
) -> Dict[str, Any]:
    """
    Process a single realization to compute and save its power spectrum.

    Args:
        realization_id: Unique identifier for the realization.
        map_file: Path to the HEALPix map file.
        mask_file: Optional path to the mask file.
        algo_name: Name of the algorithm used to generate the map (for metadata).
        lmax: Maximum multipole moment.

    Returns:
        Dictionary containing processing results and metadata.
    """
    start_time = time.time()

    try:
        # Load map
        logger.info(f"Loading map from {map_file}")
        map_data = load_map_from_fits(map_file)
        
        # Load mask if provided
        mask = None
        if mask_file and mask_file.exists():
            logger.info(f"Loading mask from {mask_file}")
            mask = load_mask_from_fits(mask_file)

        # Compute power spectrum
        l_values, cl_values = compute_power_spectrum(map_data, mask, lmax=lmax)

        # Prepare metadata
        exec_time = time.time() - start_time
        metadata = {
            "algo_name": algo_name,
            "exec_time_sec": exec_time,
            "timestamp": datetime.utcnow().isoformat(),
            "map_file": str(map_file),
            "mask_file": str(mask_file) if mask_file else None
        }

        # Save results
        meta_path = save_power_spectrum_metadata(
            realization_id, algo_name, l_values, cl_values, metadata
        )

        return {
            "success": True,
            "realization_id": realization_id,
            "algo_name": algo_name,
            "lmax": len(cl_values) - 1,
            "exec_time_sec": exec_time,
            "meta_file": meta_path
        }

    except Exception as e:
        logger.error(f"Failed to process realization {realization_id}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "realization_id": realization_id,
            "error": str(e),
            "exec_time_sec": time.time() - start_time
        }


def main():
    """
    Main entry point for the power spectra analysis script.
    
    This function is designed to be called from the command line or by a pipeline orchestrator.
    It expects to process a specific realization or a set of realizations based on configuration.
    
    For this implementation, it demonstrates processing a single example realization.
    In a full pipeline, this would be parameterized or called in a loop.
    """
    # Example configuration for demonstration
    # In production, these would be passed via command line args or config file
    realization_id = "demo_001"
    map_file = DATA_DERIVED_DIR / f"cmb_map_{realization_id}.fits"
    mask_file = DATA_DERIVED_DIR / f"mask_{realization_id}.fits"
    algo_name = "harmonic_interpolation"
    lmax = 2000

    # Check if files exist (for demo purposes)
    if not map_file.exists():
        logger.warning(f"Map file not found: {map_file}. Skipping processing.")
        logger.info("In a real pipeline, this would be triggered by upstream tasks generating the maps.")
        return

    logger.info(f"Starting power spectrum analysis for {realization_id}")
    
    result = process_realization_power_spectrum(
        realization_id=realization_id,
        map_file=map_file,
        mask_file=mask_file if mask_file.exists() else None,
        algo_name=algo_name,
        lmax=lmax
    )

    if result["success"]:
        logger.info(f"Successfully processed {realization_id}. Results saved to {result['meta_file']}")
    else:
        logger.error(f"Failed to process {realization_id}: {result.get('error', 'Unknown error')}")

    return result


if __name__ == "__main__":
    main()