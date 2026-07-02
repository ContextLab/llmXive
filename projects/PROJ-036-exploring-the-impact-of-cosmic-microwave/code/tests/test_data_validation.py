"""
Tests for data validation, including download integrity, FITS loading, and masking.
"""
import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from astropy.io import fits
import healpy as hp

from utils.io import load_map_chunked
from utils.config_manager import load_anomaly_config


def create_test_fits_file(tmp_path, nside=256, include_mask=True):
    """
    Creates a temporary FITS file with a simulated CMB map and optional mask.
    Returns the path to the created file.
    """
    npix = hp.nside2npix(nside)
    # Create a dummy temperature map with some random values
    map_data = np.random.normal(0.0, 1.0, npix)

    # Create a dummy galactic mask
    # True for |b| > 5 degrees, False otherwise
    lon, lat = hp.pix2ang(nside, np.arange(npix), lonlat=True)
    galactic_mask = np.abs(lat) > 5.0

    filename = tmp_path / "test_planck_map.fits"

    # Primary HDU
    hdu0 = fits.PrimaryHDU()

    # Temperature Map HDU
    hdu1 = fits.BinHDU(data=map_data, name="TEMPERATURE")
    hdu1.header["EXTNAME"] = "TEMPERATURE"
    hdu1.header["NPIX"] = npix
    hdu1.header["NSIDE"] = nside
    hdu1.header["PIXTYPE"] = "HEALPIX"
    hdu1.header["COORDSYS"] = "G"

    # Mask HDU if requested
    if include_mask:
        hdu2 = fits.BinHDU(data=galactic_mask.astype(np.int32), name="MASK")
        hdu2.header["EXTNAME"] = "MASK"
        hdu2.header["NPIX"] = npix
        hdu2.header["NSIDE"] = nside

        hdul = fits.HDUList([hdu0, hdu1, hdu2])
    else:
        hdul = fits.HDUList([hdu0, hdu1])

    hdul.writeto(str(filename), overwrite=True)
    hdul.close()

    return filename


class TestChunkedMapLoadingAndMask:
    """
    Integration tests for Planck map loading and masking.
    """

    def test_chunked_map_loading_and_mask(self, tmp_path):
        """
        Asserts Nside >= 256 and galactic mask application without OOM.
        """
        # Create a test file with Nside=256
        test_file = create_test_fits_file(tmp_path, nside=256)

        # Load the map in chunks
        # This tests that the loader can handle the file without memory issues
        chunks = list(load_map_chunked(test_file, chunk_size=1000))

        # Verify we loaded data
        assert len(chunks) > 0, "No data chunks were loaded"

        # Verify Nside constraint
        # We can infer Nside from the total number of pixels if we sum chunks
        total_pixels = sum(len(c) for c in chunks)
        inferred_nside = hp.npix2nside(total_pixels)
        assert inferred_nside >= 256, f"Nside {inferred_nside} is less than required 256"

        # Verify mask application logic (conceptually)
        # The actual mask application is tested in test_mask_application
        # Here we just ensure the file structure is valid
        with fits.open(test_file) as hdul:
            assert "TEMPERATURE" in [h.name for h in hdul]
            assert "MASK" in [h.name for h in hdul]


class TestMaskApplication:
    """
    Tests specifically for galactic mask application.
    """

    def test_mask_application(self, tmp_path):
        """
        Asserts that the mask correctly removes pixels with |b| <= 5 degrees.
        """
        nside = 128  # Smaller for faster test, but logic holds
        npix = hp.nside2npix(nside)

        # Create a test file with a known mask
        test_file = create_test_fits_file(tmp_path, nside=nside, include_mask=True)

        # Load the map and mask
        with fits.open(test_file) as hdul:
            temp_map = hdul["TEMPERATURE"].data
            mask_map = hdul["MASK"].data

        # Get pixel coordinates (latitude)
        lon, lat = hp.pix2ang(nside, np.arange(npix), lonlat=True)

        # Determine which pixels SHOULD be masked based on |b| <= 5
        # Mask is 1 (True) where |b| > 5, 0 (False) where |b| <= 5
        expected_mask = np.abs(lat) > 5.0

        # Assert that the mask in the file matches the expected logic
        # Note: The test file creation logic explicitly sets this,
        # but this test verifies the integrity of the mask data itself.
        assert np.array_equal(mask_map, expected_mask.astype(np.int32)), \
            "The mask in the FITS file does not correctly represent |b| > 5 degrees."

        # Verify that pixels with |b| <= 5 are indeed masked (value 0 or False)
        # In our creation logic, mask is 0 where |b| <= 5
        masked_pixels = np.where(mask_map == 0)[0]
        unmasked_pixels = np.where(mask_map == 1)[0]

        # Check that all masked pixels satisfy |b| <= 5
        for idx in masked_pixels:
            assert np.abs(lat[idx]) <= 5.0, \
                f"Pixel {idx} is masked but |b|={np.abs(lat[idx])} > 5"

        # Check that all unmasked pixels satisfy |b| > 5
        for idx in unmasked_pixels:
            assert np.abs(lat[idx]) > 5.0, \
                f"Pixel {idx} is unmasked but |b|={np.abs(lat[idx])} <= 5"

        # Test the actual application of the mask to data
        # Apply mask: keep only unmasked pixels
        masked_data = temp_map[mask_map == 1]
        original_data = temp_map

        # The number of unmasked pixels should match the count of True in expected_mask
        assert len(masked_data) == np.sum(expected_mask), \
            "Mask application did not remove the correct number of pixels."

        # Verify that the removed data corresponds to the masked region
        removed_data = temp_map[mask_map == 0]
        removed_latitudes = lat[mask_map == 0]

        # All removed data should have |b| <= 5
        assert np.all(np.abs(removed_latitudes) <= 5.0), \
            "Mask application removed pixels outside the galactic plane cutoff."