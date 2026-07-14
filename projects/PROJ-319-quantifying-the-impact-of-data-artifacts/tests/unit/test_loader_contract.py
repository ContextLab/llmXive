"""Contract tests for code/io/loader.py.

These tests verify that the loader module adheres to its specified interface
and error handling contracts.
"""
import numpy as np
import pytest
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS

# Import the module under test
from code.io.loader import (
    MetadataValidationError,
    validate_fits_headers,
    load_fits_image,
    load_fits_safe
)

def create_test_fits(path: Path, has_wcs: bool = True, has_exposure: bool = True, has_filter: bool = True):
    """Helper to create a minimal valid FITS file for testing."""
    data = np.random.rand(10, 10).astype(np.float32)
    hdu = fits.PrimaryHDU(data)

    if has_wcs:
        wcs = WCS(naxis=2)
        wcs.wcs.crpix = [5, 5]
        wcs.wcs.cdelt = [1, 1]
        wcs.wcs.crval = [0, 0]
        wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
        hdu.header.update(wcs.to_header())

    if has_exposure:
        hdu.header['EXPTIME'] = 100.0

    if has_filter:
        hdu.header['FILTER'] = 'V'

    hdu.writeto(path, overwrite=True)

def test_validate_fits_headers_missing_wcs(temp_dir):
    """Contract test: validate_fits_headers raises ValueError if WCS is missing."""
    path = temp_dir / "no_wcs.fits"
    create_test_fits(path, has_wcs=False)

    with pytest.raises(MetadataValidationError) as exc_info:
        validate_fits_headers(path)

    assert "WCS" in str(exc_info.value)

def test_validate_fits_headers_missing_exposure(temp_dir):
    """Contract test: validate_fits_headers raises ValueError if EXPTIME is missing."""
    path = temp_dir / "no_exposure.fits"
    create_test_fits(path, has_exposure=False)

    with pytest.raises(MetadataValidationError) as exc_info:
        validate_fits_headers(path)

    assert "EXPTIME" in str(exc_info.value)

def test_validate_fits_headers_missing_filter(temp_dir):
    """Contract test: validate_fits_headers raises ValueError if FILTER is missing."""
    path = temp_dir / "no_filter.fits"
    create_test_fits(path, has_filter=False)

    with pytest.raises(MetadataValidationError) as exc_info:
        validate_fits_headers(path)

    assert "FILTER" in str(exc_info.value)

def test_validate_fits_headers_success(temp_dir):
    """Contract test: validate_fits_headers returns None for valid file."""
    path = temp_dir / "valid.fits"
    create_test_fits(path)

    result = validate_fits_headers(path)
    assert result is None

def test_load_fits_image_success(temp_dir):
    """Contract test: load_fits_image returns data and header for valid file."""
    path = temp_dir / "valid.fits"
    create_test_fits(path)

    data, header = load_fits_image(path)

    assert isinstance(data, np.ndarray)
    assert isinstance(header, fits.Header)
    assert data.shape == (10, 10)

def test_load_fits_image_missing_wcs(temp_dir):
    """Contract test: load_fits_image raises ValueError if WCS is missing."""
    path = temp_dir / "no_wcs.fits"
    create_test_fits(path, has_wcs=False)

    with pytest.raises(ValueError) as exc_info:
        load_fits_image(path)

    assert "WCS" in str(exc_info.value)

def test_load_fits_safe_missing_file(temp_dir):
    """Contract test: load_fits_safe returns None for missing file."""
    path = temp_dir / "nonexistent.fits"

    result = load_fits_safe(path)
    assert result is None

def test_load_fits_safe_invalid_file(temp_dir):
    """Contract test: load_fits_safe returns None for invalid FITS."""
    path = temp_dir / "invalid.fits"
    path.write_text("not a fits file")

    result = load_fits_safe(path)
    assert result is None
