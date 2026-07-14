"""
FITS Image Loader with strict metadata validation.

This module provides functionality to load FITS images and validate
critical metadata headers (WCS, exposure time, filter). It enforces
strict validation to prevent downstream analysis on malformed data.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from astropy.io import fits
    from astropy.wcs import WCS
except ImportError:
    raise ImportError(
        "The 'astropy' package is required for FITS operations. "
        "Please install it via: pip install astropy"
    )

# Configure module logger
logger = logging.getLogger(__name__)

# Required metadata keys for validation
REQUIRED_KEYS = {
    'WCS': ['CTYPE1', 'CTYPE2', 'CRVAL1', 'CRVAL2', 'CRPIX1', 'CRPIX2', 'CDELT1', 'CDELT2'],
    'EXPOSURE': ['EXPTIME'],
    'FILTER': ['FILTER']
}

class MetadataValidationError(ValueError):
    """Custom exception for missing or invalid FITS metadata."""
    pass

def validate_fits_headers(filepath: Path) -> Dict[str, Any]:
    """
    Validate that a FITS file contains required metadata headers.

    Checks for:
    - WCS information (World Coordinate System)
    - Exposure time (EXPTIME)
    - Filter information (FILTER)

    Args:
        filepath: Path to the FITS file.

    Returns:
        dict: A dictionary containing the validated header information.

    Raises:
        FileNotFoundError: If the file does not exist.
        MetadataValidationError: If required metadata is missing or invalid.
        OSError: If the file cannot be opened as a valid FITS file.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"FITS file not found: {filepath}")

    missing_fields: List[str] = []
    header_data: Dict[str, Any] = {}

    try:
        with fits.open(filepath) as hdul:
            # Prefer the primary header or the first extension with data
            primary_header = hdul[0].header
            header = primary_header

            # If primary has no data, look for the first data extension
            if 'NAXIS' in primary_header and primary_header['NAXIS'] == 0:
                for i, hdu in enumerate(hdul):
                    if hasattr(hdu, 'data') and hdu.data is not None:
                        header = hdu.header
                        break

            # 1. Validate WCS
            wcs_fields = REQUIRED_KEYS['WCS']
            wcs_valid = True
            for field in wcs_fields:
                if field not in header:
                    missing_fields.append(f"WCS.{field}")
                    wcs_valid = False

            if wcs_valid:
                try:
                    # Attempt to construct a WCS object to ensure validity
                    wcs_obj = WCS(header)
                    if wcs_obj.naxis == 0:
                        missing_fields.append("WCS.naxis")
                        wcs_valid = False
                    else:
                        header_data['WCS'] = {
                            'valid': True,
                            'naxis': wcs_obj.naxis,
                            'crpix': [wcs_obj.wcs.crpix[0], wcs_obj.wcs.crpix[1]],
                            'cdelt': [wcs_obj.wcs.cdelt[0], wcs_obj.wcs.cdelt[1]],
                            'crval': [wcs_obj.wcs.crval[0], wcs_obj.wcs.crval[1]]
                        }
                except Exception as e:
                    missing_fields.append(f"WCS.invalid (Error: {str(e)})")
                    wcs_valid = False

            # 2. Validate Exposure Time
            exp_field = REQUIRED_KEYS['EXPOSURE'][0]
            if exp_field in header:
                header_data['EXPOSURE'] = {
                    'valid': True,
                    'value': float(header[exp_field]),
                    'unit': header.get(f'{exp_field}BUNIT', 'seconds')
                }
            else:
                missing_fields.append(f"EXPOSURE.{exp_field}")

            # 3. Validate Filter
            filter_field = REQUIRED_KEYS['FILTER'][0]
            if filter_field in header:
                header_data['FILTER'] = {
                    'valid': True,
                    'value': str(header[filter_field])
                }
            else:
                missing_fields.append(f"FILTER.{filter_field}")

    except Exception as e:
        logger.error(f"Failed to open or parse FITS file {filepath}: {e}")
        raise OSError(f"Invalid FITS file: {filepath}") from e

    # Log specific missing fields for traceability (FR-009)
    if missing_fields:
        msg = f"Validation failed for {filepath.name}: Missing required metadata fields: {', '.join(missing_fields)}"
        logger.error(msg)
        raise MetadataValidationError(msg)

    logger.info(f"Validation successful for {filepath.name}: All required fields present.")
    return header_data

def load_fits_image(filepath: Path, validate: bool = True) -> Dict[str, Any]:
    """
    Load a FITS image and optionally validate its headers.

    Args:
        filepath: Path to the FITS file.
        validate: If True, run strict metadata validation before loading data.

    Returns:
        dict: A dictionary containing:
            - 'data': numpy array of image data
            - 'header': astropy FITS header
            - 'metadata': validated metadata dictionary (if validate=True)

    Raises:
        MetadataValidationError: If validation fails and validate=True.
        FileNotFoundError: If file does not exist.
    """
    metadata = None
    if validate:
        metadata = validate_fits_headers(filepath)

    try:
        with fits.open(filepath) as hdul:
            # Find the first HDU with data
            data_hdu = None
            for hdu in hdul:
                if hdu.data is not None:
                    data_hdu = hdu
                    break

            if data_hdu is None:
                raise ValueError(f"No image data found in FITS file: {filepath}")

            return {
                'data': data_hdu.data,
                'header': data_hdu.header,
                'metadata': metadata,
                'filename': str(filepath)
            }
    except Exception as e:
        logger.error(f"Error loading image data from {filepath}: {e}")
        raise

def load_fits_safe(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    Attempt to load a FITS file, returning None if validation fails.
    Useful for batch processing where individual file failures should not stop the pipeline.

    Args:
        filepath: Path to the FITS file.

    Returns:
        dict or None: Loaded data dictionary if successful, None if validation failed.
    """
    try:
        return load_fits_image(filepath, validate=True)
    except (MetadataValidationError, FileNotFoundError, OSError) as e:
        logger.warning(f"Skipping {filepath} due to error: {e}")
        return None