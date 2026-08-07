"""
Data loader module for acquiring and preprocessing Planck CMB data.

Implements download, validation, masking, and resolution downgrade
of the Planck SMICA CMB map.
"""
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import healpy as hp
import numpy as np
import requests
from requests.exceptions import RequestException, Timeout

from config import ensure_directories
from logging_config import get_logger

# Constants for Planck 2018 SMICA map
PLANCK_URL = "https://pla.esac.esa.int/pla/aio/product?action=download&filename=COM_CMB_ILU_SMICA_R3.00_Hpx.fits"
EXPECTED_CHECKSUM = "a3c8e3e6c3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3"  # Placeholder, actual checksum from spec
NSIDE_HIGH = 2048
NSIDE_LOW = 128
MASK_URL = "https://pla.esac.esa.int/pla/aio/product?action=download&filename=COM_Mask-General_R2.02.fits"
MASK_CHECKSUM = "b4c8e3e6c3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3"  # Placeholder

logger = get_logger(__name__)


def download_planck_map(output_path: Path, force_download: bool = False) -> Path:
    """
    Download the Planck SMICA CMB map from the ESA archive.
    
    Args:
        output_path: Path where the file should be saved.
        force_download: If True, re-download even if file exists.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        ConnectionError: If the URL is unavailable or network fails.
        ValueError: If checksum validation fails.
    """
    ensure_directories()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force_download:
        logger.info(f"File already exists: {output_path}")
        return output_path

    logger.info(f"Downloading Planck SMICA map from {PLANCK_URL}...")
    try:
        response = requests.get(PLANCK_URL, stream=True, timeout=300)
        response.raise_for_status()
    except Timeout:
        raise ConnectionError(f"Timeout while downloading from {PLANCK_URL}")
    except RequestException as e:
        raise ConnectionError(f"Failed to download from {PLANCK_URL}: {e}")

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Validate checksum
    actual_checksum = _calculate_sha256(output_path)
    # In a real implementation, EXPECTED_CHECKSUM would be the known good hash
    # For this implementation, we simulate a check that would fail if the hash didn't match
    if actual_checksum != EXPECTED_CHECKSUM:
        # In a real scenario, we would have the correct checksum.
        # If this fails, it indicates data corruption or wrong file.
        # We raise an error to prevent proceeding with bad data.
        logger.error(f"Checksum mismatch for {output_path}")
        logger.error(f"Expected: {EXPECTED_CHECKSUM}")
        logger.error(f"Actual:   {actual_checksum}")
        os.remove(output_path)
        raise ValueError(f"Checksum mismatch for downloaded file {output_path}. Data may be corrupted.")

    logger.info(f"Download and validation successful: {output_path}")
    return output_path


def apply_galactic_mask(input_path: Path, output_path: Path, retention_threshold: float = 0.95) -> Path:
    """
    Apply the Commander mask to the CMB map to exclude foregrounds.
    
    Args:
        input_path: Path to the unmasked CMB map.
        output_path: Path to save the masked map.
        retention_threshold: Minimum fraction of sky to retain (default 0.95).
        
    Returns:
        Path to the masked map.
        
    Raises:
        ValueError: If the unmasked sky retention is below the threshold.
    """
    ensure_directories()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Applying galactic mask to {input_path}...")
    m = hp.read_map(input_path, field=[0, 1, 2])
    mask = hp.read_map(MASK_URL, field=0) # Assuming mask is downloaded similarly

    # Apply mask (0 where masked out, 1 where kept)
    # Healpy mask application: multiply map by mask
    masked_m = m * mask

    # Calculate statistics
    total_pixels = hp.nside2npix(2048)
    masked_pixels = np.sum(mask == 0)
    unmasked_pixels = np.sum(mask == 1)
    retention_rate = unmasked_pixels / total_pixels

    stats = {
        "total_pixels": int(total_pixels),
        "masked_pixels": int(masked_pixels),
        "unmasked_pixels": int(unmasked_pixels),
        "retention_rate": float(retention_rate)
    }

    # Log stats to file
    stats_path = Path("data/processed/mask_stats.json")
    import json
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Mask stats: {stats}")

    if retention_rate < retention_threshold:
        raise ValueError(
            f"Mask retention rate ({retention_rate:.4f}) is below threshold "
            f"({retention_threshold}). Aborting to ensure sufficient sky coverage."
        )

    hp.write_map(output_path, masked_m, overwrite=True)
    logger.info(f"Masked map saved to {output_path}")
    return output_path


def downgrade_resolution(input_path: Path, output_path: Path) -> Path:
    """
    Downgrade the resolution of a CMB map from Nside=2048 to Nside=128.
    
    Args:
        input_path: Path to the high-resolution map.
        output_path: Path to save the downgraded map.
        
    Returns:
        Path to the downgraded map.
        
    Raises:
        ValueError: If the input map has invalid values (NaN/inf).
    """
    ensure_directories()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downgrading resolution of {input_path} to Nside=128...")
    m = hp.read_map(input_path, field=[0, 1, 2])

    # Check for NaN/inf
    if np.any(np.isnan(m)) or np.any(np.isinf(m)):
        raise ValueError("Input map contains NaN or Inf values. Cannot downgrade.")

    # Downgrade using healpy's ud_grade
    # Note: ud_grade performs a simple average, which is appropriate for masked maps
    # if the mask was applied correctly.
    m_low = hp.ud_grade(m, nside_out=NSIDE_LOW)

    # Verify output
    if np.any(np.isnan(m_low)) or np.any(np.isinf(m_low)):
        raise ValueError("Downgraded map contains NaN or Inf values.")

    hp.write_map(output_path, m_low, overwrite=True)
    logger.info(f"Downgraded map saved to {output_path}")
    return output_path


def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()