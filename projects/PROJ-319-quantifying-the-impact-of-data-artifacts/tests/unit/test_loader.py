"""
Contract tests for code/io/loader.py.

These tests verify the interface contracts and error handling behavior
of the FITS loader module, specifically ensuring that missing critical
metadata (WCS, exposure time, filter) raises appropriate errors.
"""
import pytest
import numpy as np
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS

# Import the module under test
# Note: We assume the project root is added to sys.path or this is run via pytest --rootdir=code
from io.loader import load_fits_image, MetadataValidationError


def create_test_fits_with_missing_metadata(tmp_path: Path, missing_field: str) -> str:
    """
    Helper to create a minimal FITS file with specific metadata removed.
    
    Args:
        tmp_path: Temporary directory path
        missing_field: One of 'WCS', 'EXPTIME', 'FILTER'
        
    Returns:
        Path to the created FITS file
    """
    # Create a simple 2D array
    data = np.random.rand(100, 100).astype(np.float32)
    
    # Create primary HDU
    hdu = fits.PrimaryHDU(data)
    
    # Add standard metadata
    hdu.header['TELESCOP'] = 'HST'
    hdu.header['INSTRUME'] = 'ACS'
    
    if missing_field != 'EXPTIME':
        hdu.header['EXPTIME'] = 1000.0
    if missing_field != 'FILTER':
        hdu.header['FILTER'] = 'F814W'
        
    # Handle WCS specifically
    if missing_field == 'WCS':
        # Do not add any WCS keywords (CTYPE1, CRPIX1, etc.)
        pass
    else:
        # Add a minimal valid WCS
        wcs = WCS(naxis=2)
        wcs.wcs.crpix = [50, 50]
        wcs.wcs.cdelt = [0.1, 0.1]
        wcs.wcs.crval = [0, 0]
        wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
        wcs.wcs.cunit = ['deg', 'deg']
        hdu.header.update(wcs.to_header())
        
    fits_file = tmp_path / "test_missing.fits"
    hdu.writeto(fits_file, overwrite=True)
    return str(fits_file)


class TestLoaderWCSValidation:
    """Tests for WCS validation requirements (FR-009)."""
    
    def test_loader_raises_on_missing_wcs(self, tmp_path: Path):
        """
        Contract test: loader.load() must raise ValueError when WCS metadata is missing.
        
        This directly tests FR-009: "The system shall abort on missing metadata
        and log the specific missing fields."
        """
        fits_path = create_test_fits_with_missing_metadata(tmp_path, missing_field='WCS')
        
        with pytest.raises(MetadataValidationError) as exc_info:
            load_fits_image(fits_path)
        
        # Verify the error message mentions the missing field
        assert "WCS" in str(exc_info.value).upper() or "WCS" in str(exc_info.value)
        
    def test_loader_raises_on_missing_exptime(self, tmp_path: Path):
        """
        Contract test: loader.load() must raise ValueError when EXPTIME is missing.
        """
        fits_path = create_test_fits_with_missing_metadata(tmp_path, missing_field='EXPTIME')
        
        with pytest.raises(MetadataValidationError) as exc_info:
            load_fits_image(fits_path)
        
        assert "EXPTIME" in str(exc_info.value).upper()
        
    def test_loader_raises_on_missing_filter(self, tmp_path: Path):
        """
        Contract test: loader.load() must raise ValueError when FILTER is missing.
        """
        fits_path = create_test_fits_with_missing_metadata(tmp_path, missing_field='FILTER')
        
        with pytest.raises(MetadataValidationError) as exc_info:
            load_fits_image(fits_path)
        
        assert "FILTER" in str(exc_info.value).upper()
        
    def test_loader_succeeds_with_complete_metadata(self, tmp_path: Path):
        """
        Contract test: loader.load() should succeed when all metadata is present.
        """
        fits_path = create_test_fits_with_missing_metadata(tmp_path, missing_field=None)
        
        # Should not raise
        result = load_fits_image(fits_path)
        
        assert result is not None
        assert 'data' in result
        assert 'metadata' in result
        assert isinstance(result['data'], np.ndarray)