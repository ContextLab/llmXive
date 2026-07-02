"""
Data Download and Processing Module for CMB Analysis.

Handles downloading Planck CMB maps, validating checksums, 
validating FITS headers, and applying galactic masks.
"""
import os
import sys
import time
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import requests
from astropy.io import fits
from astropy.wcs import WCS
import yaml

# Project local imports
from utils.config_manager import load_yaml_config
from utils.logging_config import get_logger, check_memory_limit
from utils.io import load_fits_header_with_astropy, validate_fits_nside

# Configure logging
logger = get_logger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds
GALACTIC_LATITUDE_THRESHOLD = 5.0  # degrees

def load_checksums(config_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load expected SHA256 checksums from configuration.
    
    Args:
        config_path: Path to planck_checksums.yaml. Defaults to config/planck_checksums.yaml.
        
    Returns:
        Dictionary mapping filenames to their expected SHA256 hashes.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is malformed.
    """
    if config_path is None:
        config_path = Path("config/planck_checksums.yaml")
        
    if not config_path.exists():
        raise FileNotFoundError(f"Checksum config not found at {config_path}")
        
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    return config.get('checksums', {})

def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculate SHA256 hash of a file in chunks to handle large files.
    
    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read (default 8KB).
        
    Returns:
        Hexadecimal SHA256 hash string.
    """
    sha256_hash = hashlib.sha256()
    logger.info(f"Calculating hash for {file_path}...")
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
            
    return sha256_hash.hexdigest()

def download_with_retry(
    url: str, 
    dest_path: Path, 
    expected_hash: Optional[str] = None
) -> Path:
    """
    Download a file with retry logic and optional hash validation.
    
    Args:
        url: Source URL.
        dest_path: Destination file path.
        expected_hash: Optional expected SHA256 hash.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        RuntimeError: If download fails after retries or hash mismatch.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Downloading {url} (Attempt {attempt}/{MAX_RETRIES})")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 10%
                        if total_size > 0 and downloaded % (total_size // 10) < 8192:
                            percent = (downloaded / total_size) * 100
                            logger.debug(f"Download progress: {percent:.1f}%")
            
            # Validate hash if provided
            if expected_hash:
                actual_hash = calculate_file_hash(dest_path)
                if actual_hash.lower() != expected_hash.lower():
                    raise RuntimeError(
                        f"Hash mismatch for {dest_path}. "
                        f"Expected: {expected_hash}, Got: {actual_hash}"
                    )
            
            logger.info(f"Successfully downloaded and validated {dest_path}")
            return dest_path
            
        except requests.RequestException as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
            else:
                raise RuntimeError(f"Failed to download {url} after {MAX_RETRIES} attempts") from e
                
        except RuntimeError as e:
            # Hash mismatch or other critical error
            if dest_path.exists():
                dest_path.unlink()
            raise e

def validate_fits_header(
    file_path: Path, 
    min_nside: int = 256,
    anomaly_coords: Optional[Dict[str, Tuple[float, float]]] = None
) -> bool:
    """
    Validate FITS header for CMB map requirements.
    
    Args:
        file_path: Path to the FITS file.
        min_nside: Minimum required Nside resolution.
        anomaly_coords: Optional dict of anomaly names to (lon, lat) tuples to verify presence.
        
    Returns:
        True if valid, raises exception otherwise.
        
    Raises:
        ValueError: If Nside is too low or anomaly regions missing.
        OSError: If file cannot be opened.
    """
    logger.info(f"Validating FITS header for {file_path}")
    
    try:
        header = load_fits_header_with_astropy(file_path)
        nside = validate_fits_nside(header)
        
        if nside < min_nside:
            raise ValueError(
                f"Nside {nside} is below minimum required {min_nside}"
            )
        
        logger.info(f"FITS header valid. Nside: {nside}")
        
        # Optional: Check for known anomaly coordinates
        if anomaly_coords:
            wcs = WCS(header)
            for name, (lon, lat) in anomaly_coords.items():
                # Convert to pixel
                try:
                    px, py = wcs.wcs_world2pix(lon, lat, 0)
                    if 0 <= px < header['NAXIS1'] and 0 <= py < header['NAXIS2']:
                        logger.info(f"Verified anomaly region '{name}' at ({lon}, {lat}) is within map bounds.")
                    else:
                        logger.warning(f"Anomaly region '{name}' at ({lon}, {lat}) is outside map bounds.")
                except Exception as e:
                    logger.warning(f"Could not verify anomaly region '{name}': {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"FITS validation failed: {e}")
        raise

def apply_galactic_mask(
    input_path: Path, 
    output_path: Path, 
    latitude_threshold: float = GALACTIC_LATITUDE_THRESHOLD
) -> Path:
    """
    Apply a galactic mask to a CMB FITS map, removing pixels with |b| <= threshold.
    
    The mask sets pixels within the galactic plane (|b| <= latitude_threshold) to NaN.
    
    Args:
        input_path: Path to input FITS file.
        output_path: Path for output masked FITS file.
        latitude_threshold: Galactic latitude threshold in degrees (default 5.0).
        
    Returns:
        Path to the output masked file.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required WCS information is missing.
    """
    logger.info(f"Applying galactic mask (|b| > {latitude_threshold}°) to {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Open FITS file
    hdul = fits.open(input_path, memmap=True)
    
    # Identify the primary data extension (usually the first extension for Planck maps)
    # Planck maps are typically in the first HDU extension with a 'MAP' or similar name
    data_hdu = None
    for hdu in hdul:
        if hdu.data is not None and hdu.data.ndim >= 2:
            data_hdu = hdu
            break
    
    if data_hdu is None:
        raise ValueError("Could not find data extension in FITS file")
        
    data = data_hdu.data.copy()
    header = data_hdu.header.copy()
    
    # Check for WCS information
    if 'CRPIX1' not in header or 'CRPIX2' not in header or 'CTYPE1' not in header:
        # Try to construct WCS from header if possible, otherwise fail
        try:
            wcs = WCS(header)
        except Exception:
            hdul.close()
            raise ValueError("FITS file missing required WCS information for masking")
    else:
        wcs = WCS(header)
    
    # Generate coordinate grids
    ny, nx = data.shape
    y_indices, x_indices = np.meshgrid(np.arange(ny), np.arange(nx), indexing='ij')
    
    # Transform pixel coordinates to world coordinates (Galactic)
    # Ensure we are using Galactic coordinates (CTYPE should be GLON/GLAT)
    # If not, we might need to transform, but Planck data is usually Galactic
    lon, lat = wcs.wcs_pix2world(x_indices, y_indices, 0)
    
    # Apply mask: set pixels with |b| <= threshold to NaN
    # Note: lat is in degrees
    mask = np.abs(lat) <= latitude_threshold
    masked_data = np.where(mask, np.nan, data)
    
    # Update header to indicate masking
    header['COMMENT'] = f"Galactic mask applied: |b| > {latitude_threshold} degrees"
    header['MASKED'] = True
    header['MASK_LAT'] = latitude_threshold
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hdu_out = fits.PrimaryHDU(masked_data, header=header)
    hdu_out.writeto(output_path, overwrite=True)
    
    hdul.close()
    
    # Log statistics
    total_pixels = data.size
    masked_pixels = np.sum(mask)
    logger.info(f"Mask applied: {masked_pixels}/{total_pixels} pixels masked ({100*masked_pixels/total_pixels:.2f}%)")
    
    return output_path

def main():
    """
    Main entry point for data download and processing.
    
    This script:
    1. Downloads Planck CMB maps (Commander/SMICA) from the Planck Legacy Archive.
    2. Validates checksums against config/planck_checksums.yaml.
    3. Validates FITS headers (Nside >= 256).
    4. Applies a galactic mask (|b| > 5°).
    """
    logger.info("Starting CMB Data Download and Processing Pipeline")
    
    # Load configuration
    try:
        checksums = load_checksums()
        # For demo purposes, if no checksums are found, we might skip hash validation
        # In production, this should be strict
        if not checksums:
            logger.warning("No checksums found in config. Skipping hash validation.")
    except Exception as e:
        logger.error(f"Failed to load checksums: {e}")
        # Continue with download but skip hash validation if config is missing
        checksums = {}
        
    # Define download targets (Example URLs for Planck PR3 Commander/SMICA)
    # In a real scenario, these would be read from a config file
    download_targets = [
        {
            "name": "commander_mask",
            "url": "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_Mask_CMB_2048_R3.00.fits",
            "output": "data/raw/planck_commander_mask.fits"
        },
        {
            "name": "smica_map",
            "url": "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CMB_MILMAP_2048_R3.00.fits",
            "output": "data/raw/planck_smica_map.fits"
        }
    ]
    
    # Load anomaly coordinates if available
    anomaly_coords = None
    try:
        anomaly_config = load_yaml_config(Path("config/anomaly.yaml"))
        if anomaly_config and 'regions' in anomaly_config:
            anomaly_coords = {
                name: (region['lon'], region['lat']) 
                for name, region in anomaly_config['regions'].items()
            }
    except Exception as e:
        logger.warning(f"Could not load anomaly coordinates: {e}")
    
    for target in download_targets:
        name = target['name']
        url = target['url']
        output_path = Path(target['output'])
        
        expected_hash = checksums.get(output_path.name)
        
        try:
            # 1. Download
            if expected_hash:
                logger.info(f"Downloading {name} with hash validation")
            else:
                logger.info(f"Downloading {name} without hash validation")
                
            download_with_retry(url, output_path, expected_hash)
            
            # 2. Validate Header
            validate_fits_header(output_path, min_nside=256, anomaly_coords=anomaly_coords)
            
            # 3. Apply Galactic Mask
            masked_path = output_path.parent / f"{output_path.stem}_masked.fits"
            apply_galactic_mask(output_path, masked_path)
            
            logger.info(f"Processing complete for {name}")
            
        except Exception as e:
            logger.error(f"Failed to process {name}: {e}")
            # In a real pipeline, we might want to continue or abort based on criticality
            # For now, we log and continue to next target
            continue
            
    logger.info("Data Download and Processing Pipeline finished")

if __name__ == "__main__":
    main()
