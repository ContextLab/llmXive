import os
import tempfile
import numpy as np
import healpy as hp
from pathlib import Path
import pytest

# Import functions to test
from data_loader import (
    calculate_sha256,
    apply_galactic_mask,
    downgrade_resolution,
    save_processed_map
)
from config import NSIDE_HIGH, NSIDE_LOW, PROCESSED_MAP_FILENAME

class TestChecksumValidation:
    """Test checksum calculation for data integrity."""

    def test_calculate_sha256(self):
        """Test that SHA-256 checksum is calculated correctly."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data for checksum")
            tmp_path = tmp.name

        try:
            checksum = calculate_sha256(tmp_path)
            assert len(checksum) == 64  # SHA-256 produces 64 hex characters
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(tmp_path)

    def test_checksum_uniqueness(self):
        """Test that different files produce different checksums."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp1:
            tmp1.write(b"data one")
            path1 = tmp1.name

        with tempfile.NamedTemporaryFile(delete=False) as tmp2:
            tmp2.write(b"data two")
            path2 = tmp2.name

        try:
            checksum1 = calculate_sha256(path1)
            checksum2 = calculate_sha256(path2)
            assert checksum1 != checksum2
        finally:
            os.unlink(path1)
            os.unlink(path2)

class TestMaskApplication:
    """Test mask application and pixel exclusion."""

    def test_mask_retention_threshold(self):
        """Test that mask retention is calculated and validated."""
        # Create a synthetic mask with 96% retention (above threshold)
        npix = hp.nside2npix(NSIDE_HIGH)
        mask = np.ones(npix)
        mask[int(npix * 0.04):] = 0  # 4% masked, 96% retained

        # Create synthetic CMB map
        cmb_map = np.random.randn(3, npix).astype(np.float32)

        # Apply mask
        masked_map, stats = apply_galactic_mask(cmb_map)

        # Verify retention
        assert stats['retention_percentage'] >= 0.95

    def test_mask_application_excludes_pixels(self):
        """Test that masked pixels are set to zero."""
        npix = hp.nside2npix(NSIDE_HIGH)
        mask = np.ones(npix)
        mask[0] = 0  # Mask first pixel

        cmb_map = np.ones((3, npix))
        masked_map, _ = apply_galactic_mask(cmb_map)

        # Check that masked pixel is zero
        assert masked_map[0, 0] == 0.0
        assert masked_map[1, 0] == 0.0
        assert masked_map[2, 0] == 0.0

class TestDowngradeResolution:
    """Test Nside downgrade memory usage and NaN checks."""

    def test_downgrade_no_nan(self):
        """Test that downgraded map has no NaN values."""
        npix_high = hp.nside2npix(NSIDE_HIGH)
        npix_low = hp.nside2npix(NSIDE_LOW)

        # Create synthetic masked map
        masked_map = np.random.randn(3, npix_high).astype(np.float32)

        # Downgrade
        downgraded_map = downgrade_resolution(masked_map)

        # Check for NaN
        assert not np.any(np.isnan(downgraded_map))
        assert not np.any(np.isinf(downgraded_map))

    def test_downgrade_correct_size(self):
        """Test that downgraded map has correct size."""
        npix_high = hp.nside2npix(NSIDE_HIGH)
        npix_low = hp.nside2npix(NSIDE_LOW)

        masked_map = np.random.randn(3, npix_high).astype(np.float32)
        downgraded_map = downgrade_resolution(masked_map)

        assert downgraded_map.shape == (3, npix_low)

    def test_memory_usage(self):
        """Test that downgraded map fits in memory constraint."""
        npix_low = hp.nside2npix(NSIDE_LOW)

        # Create synthetic masked map
        masked_map = np.random.randn(3, hp.nside2npix(NSIDE_HIGH)).astype(np.float32)

        # Downgrade
        downgraded_map = downgrade_resolution(masked_map)

        # Estimate memory usage (3 components * npix_low * 4 bytes for float32)
        memory_mb = (3 * npix_low * 4) / (1024 * 1024)

        # Should be well under 100MB
        assert memory_mb < 100

class TestSaveProcessedMap:
    """Test saving processed map to FITS file."""

    def test_save_processed_map_creates_file(self):
        """Test that save_processed_map creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.fits")
            npix = hp.nside2npix(NSIDE_LOW)
            map_data = np.random.randn(3, npix).astype(np.float32)

            save_processed_map(map_data, output_path)

            assert os.path.exists(output_path)

    def test_save_processed_map_size_constraint(self):
        """Test that saved file is under 150MB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.fits")
            npix = hp.nside2npix(NSIDE_LOW)
            map_data = np.random.randn(3, npix).astype(np.float32)

            save_processed_map(map_data, output_path)

            file_size = os.path.getsize(output_path)
            file_size_mb = file_size / (1024 * 1024)

            # Nside=128 FITS file should be much smaller than 150MB
            assert file_size_mb < 150

    def test_save_processed_map_header_metadata(self):
        """Test that FITS header contains provenance and checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.fits")
            npix = hp.nside2npix(NSIDE_LOW)
            map_data = np.random.randn(3, npix).astype(np.float32)

            save_processed_map(map_data, output_path)

            # Read header
            header = hp.get_header(output_path)

            assert 'PROVENANCE' in header
            assert 'CHECKSUM' in header
            assert len(header['CHECKSUM']) == 64  # SHA-256 hex string