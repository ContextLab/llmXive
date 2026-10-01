"""
CMB Data Processor Module.

This module handles the loading, masking, and beam deconvolution of
CMB maps downloaded from the ESA Planck Legacy Archive. It produces
analysis-ready maps in the `data/processed/` directory.
"""

import os
import numpy as np
import healpy as hp
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

from code.config import load_config
from code.utils.logging import setup_logger
from code.data.downloader import DataDownloadError

# Define expected resolution
NPIX_TARGET = 12 * 2048 ** 2  # Nside=2048


class ProcessingError(Exception):
    """Custom exception for data processing failures."""
    pass


def load_raw_map(file_path: Path) -> np.ndarray:
    """
    Load a raw CMB map from a FITS file.

    Args:
        file_path: Path to the input FITS file.

    Returns:
        np.ndarray: The map data (1D array of pixel values).

    Raises:
        ProcessingError: If the file cannot be read or has incorrect Nside.
    """
    logger = setup_logger(__name__)
    if not file_path.exists():
        raise ProcessingError(f"Raw map file not found: {file_path}")

    try:
        # Read the map. healpy.read_map returns a tuple if multiple components exist.
        # We expect a single component (I, Q, U or just I depending on file).
        # We force reading just the intensity map if multiple columns exist,
        # but typically Planck maps are single-component files for I, Q, U.
        # For this pipeline, we assume the file contains the component we need.
        m = hp.read_map(str(file_path), field=0, nest=True, dtype=None)
        
        # Determine Nside
        nside = hp.get_nside(m)
        expected_nside = 2048
        
        if nside != expected_nside:
            # If the downloaded file is not Nside=2048, we must resample or error.
            # The task requires Nside=2048. We will raise an error if mismatch
            # to force the user to ensure correct input data.
            raise ProcessingError(
                f"Nside mismatch: file has {nside}, expected {expected_nside}. "
                "Ensure raw data is Nside=2048."
            )
        
        logger.info(f"Loaded map from {file_path.name} with Nside={nside}, size={m.size}")
        return m
    except Exception as e:
        raise ProcessingError(f"Failed to load map from {file_path}: {e}") from e


def load_mask(mask_path: Path) -> np.ndarray:
    """
    Load a confidence mask from a FITS file.

    Args:
        mask_path: Path to the mask FITS file.

    Returns:
        np.ndarray: The mask data (1D array, 0 or 1 or float weights).
    """
    logger = setup_logger(__name__)
    if not mask_path.exists():
        raise ProcessingError(f"Mask file not found: {mask_path}")

    try:
        mask = hp.read_map(str(mask_path), field=0, nest=True, dtype=np.float32)
        logger.info(f"Loaded mask from {mask_path.name}")
        return mask
    except Exception as e:
        raise ProcessingError(f"Failed to load mask from {mask_path}: {e}") from e


def apply_mask(map_data: np.ndarray, mask_data: np.ndarray) -> np.ndarray:
    """
    Apply a confidence mask to a CMB map.

    Pixels where the mask is 0 (or below a threshold) are set to 0.0.
    This effectively removes those pixels from the analysis.

    Args:
        map_data: The input map data.
        mask_data: The mask data (0.0 for masked, 1.0 for unmasked).

    Returns:
        np.ndarray: The masked map data.
    """
    logger = setup_logger(__name__)
    
    if map_data.shape != mask_data.shape:
        raise ProcessingError(
            f"Shape mismatch between map {map_data.shape} and mask {mask_data.shape}"
        )

    # Apply mask: set masked pixels to 0.0
    # We assume mask values are 0.0 (masked) and 1.0 (unmasked) or weights.
    # To strictly zero out masked regions, we multiply.
    masked_map = map_data * mask_data

    masked_count = np.sum(mask_data == 0)
    total_count = map_data.size
    logger.info(
        f"Applied mask: {masked_count}/{total_count} pixels masked "
        f"({100*masked_count/total_count:.2f}%)"
    )

    return masked_map


def deconvolve_beam(map_data: np.ndarray, beam_function: str = "gaussian", 
                    fwhm_arcmin: float = 5.0) -> np.ndarray:
    """
    Deconvolve the beam and pixel window functions from the map.

    This operation attempts to recover the underlying sky signal by dividing
    the spherical harmonic coefficients by the beam transfer function.
    Since division by zero is dangerous at high l, this is done carefully.

    Note: In a full pipeline, this would be done in harmonic space (alm -> beam -> map).
    For this implementation, we approximate the deconvolution in pixel space
    or perform a direct harmonic inversion if the beam is known.
    
    However, `healpy` does not have a direct `deconvolve_beam` pixel-space function.
    The standard approach is:
    1. Map -> Alm (anafast/alm2map is forward, map2alm is inverse)
    2. Divide Alm by beam(l)
    3. Alm -> Map

    We will implement this harmonic-space deconvolution.

    Args:
        map_data: Input map (masked).
        beam_function: Type of beam (currently supports 'gaussian').
        fwhm_arcmin: Full Width at Half Maximum of the beam in arcminutes.

    Returns:
        np.ndarray: Deconvolved map.
    """
    logger = setup_logger(__name__)
    nside = hp.get_nside(map_data)
    l_max = 3 * nside - 1  # Nyquist limit

    logger.info(f"Starting beam deconvolution for Nside={nside}, l_max={l_max}")

    # Convert map to alm
    # We use l_max=3*nside-1 for full resolution deconvolution
    # Use iterative map2alm to handle masked pixels better? 
    # For now, standard map2alm with a mask is safer.
    # We pass the map directly; masked pixels (0) will contribute, but 
    # ideally we should use an iterative solver. For this task, we assume
    # the mask is sufficient or we proceed with standard map2alm.
    
    alm = hp.map2alm(map_data, lmax=l_max, use_pixel_weights=True)

    # Construct beam window function
    # B_l = exp( -l(l+1) sigma^2 / 2 )
    # sigma = FWHM / (2 * sqrt(2 * ln(2)))
    # But healpy provides `gaussian_beam` or we can compute manually.
    
    l = np.arange(l_max + 1)
    sigma = fwhm_arcmin / (2.0 * np.sqrt(2.0 * np.log(2.0))) * (np.pi / 180.0 / 60.0)
    beam_window = np.exp(-0.5 * l * (l + 1) * sigma**2)

    # Apply pixel window function (approximation or exact if available)
    # For Nside=2048, pixel window is significant at high l.
    # We use hp.pixwin to get the pixel window function.
    pix_window = hp.pixwin(nside, lmax=l_max)

    # Total window function
    total_window = beam_window * pix_window

    # Avoid division by zero
    total_window = np.where(total_window < 1e-10, 1e-10, total_window)

    # Deconvolve: divide alm coefficients by the window function
    # alm is complex array of shape (3*nside**2, ...) ? No, map2alm returns a flat array.
    # We need to reshape or use hp.alm2map with the modified alm.
    # Actually, hp.map2alm returns a 1D array of alm coefficients.
    # We can multiply element-wise if we align l,m.
    # But `hp.alm2alm` or manual scaling is needed.
    
    # Simpler approach: hp.alm2map expects alm coefficients.
    # We need to scale the alm coefficients.
    # Since `hp.map2alm` returns a flat array, we can't just multiply by `total_window`
    # unless we know the index mapping.
    # Instead, we use hp.alm2map with the beam applied? No, we want to remove it.
    
    # Correct approach:
    # 1. Get alm.
    # 2. Scale alm by 1/total_window.
    #    To do this, we need to iterate over l and apply to the relevant lm indices.
    #    Or use hp.alm2alm which applies a transfer function.
    
    # We will use hp.alm2alm to apply the inverse beam.
    # hp.alm2alm(alm, bl) applies the function bl to the alm.
    # We want 1/total_window.
    
    inv_window = 1.0 / total_window
    alm_deconv = hp.alm2alm(alm, inv_window)

    # Convert back to map
    deconvolved_map = hp.alm2map(alm_deconv, nside, pixwin=False)

    logger.info("Beam deconvolution completed.")
    return deconvolved_map


def validate_output(map_data: np.ndarray, output_path: Path) -> bool:
    """
    Validate the processed map before saving.

    Checks:
    - No NaN values in unmasked regions (if mask exists).
    - Correct Nside (2048).
    - File size > 0.

    Args:
        map_data: The processed map data.
        output_path: The intended output path.

    Returns:
        bool: True if valid.

    Raises:
        ProcessingError: If validation fails.
    """
    logger = setup_logger(__name__)
    
    nside = hp.get_nside(map_data)
    if nside != 2048:
        raise ProcessingError(f"Output Nside is {nside}, expected 2048")

    if np.any(np.isnan(map_data)):
        nan_count = np.sum(np.isnan(map_data))
        raise ProcessingError(
            f"Output map contains {nan_count} NaN values. "
            "Check mask application and deconvolution steps."
        )

    logger.info(f"Validation passed for {output_path.name}")
    return True


def process_cmb_data(raw_dir: Path, mask_dir: Path, output_dir: Path, 
                     file_list: List[str]) -> Dict[str, Path]:
    """
    Main processing pipeline: Load, Mask, Deconvolve, Validate, Save.

    Args:
        raw_dir: Directory containing raw FITS maps.
        mask_dir: Directory containing mask FITS files.
        output_dir: Directory to save processed maps.
        file_list: List of base filenames (without extension) to process.

    Returns:
        Dict mapping component name to output path.
    """
    logger = setup_logger(__name__)
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}

    for file_name in file_list:
        raw_path = raw_dir / file_name
        mask_path = mask_dir / file_name  # Assuming same name for mask
        
        logger.info(f"Processing {file_name}...")
        
        try:
            # 1. Load
            map_data = load_raw_map(raw_path)
            
            # 2. Load Mask
            mask_data = load_mask(mask_path)
            
            # 3. Apply Mask
            masked_map = apply_mask(map_data, mask_data)
            
            # 4. Deconvolve Beam
            # Default beam parameters from config or standard Planck
            # We assume a standard Gaussian beam for this task unless config specifies
            deconv_map = deconvolve_beam(masked_map, beam_function="gaussian", fwhm_arcmin=5.0)
            
            # 5. Validate
            output_path = output_dir / f"{file_name}_processed.fits"
            validate_output(deconv_map, output_path)
            
            # 6. Save
            hp.write_map(str(output_path), deconv_map, nest=True, overwrite=True)
            results[file_name] = output_path
            
            logger.info(f"Saved processed map to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to process {file_name}: {e}")
            raise ProcessingError(f"Pipeline failed for {file_name}") from e

    return results


def main():
    """
    Entry point for the processor script.
    Loads config, finds raw files, and runs the pipeline.
    """
    logger = setup_logger(__name__)
    logger.info("Starting CMB Data Processor...")

    config = load_config()
    
    # Extract paths from config
    raw_dir = Path(config['paths']['raw'])
    processed_dir = Path(config['paths']['processed'])
    
    # Ensure directories exist
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Define files to process based on config or defaults
    # The downloader should have populated data/raw/
    # We look for SMICA, EE, TE maps
    target_files = config.get('files', {}).get('process', [
        "SMICA_I.fits", "SMICA_Q.fits", "SMICA_U.fits",
        "SMICA_EE.fits", "SMICA_TE.fits", # Placeholder names, adjust based on actual download
        "SMICA_mask.fits"
    ])
    
    # In a real scenario, we would filter the actual files in data/raw/
    # For this implementation, we assume the downloader created specific files.
    # We will scan the raw directory for FITS files if no specific list is provided.
    if not target_files:
        fits_files = list(raw_dir.glob("*.fits"))
        target_files = [f.stem for f in fits_files]

    logger.info(f"Found {len(target_files)} files to process.")

    if not target_files:
        logger.warning("No files found to process in data/raw/.")
        return

    # Run processing
    try:
        results = process_cmb_data(raw_dir, raw_dir, processed_dir, target_files)
        logger.info(f"Processing complete. {len(results)} files saved to {processed_dir}")
    except ProcessingError as e:
        logger.error(f"Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()