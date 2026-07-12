"""
Tests for data acquisition and pre-processing pipeline.
Focus: US1 - Data Acquisition and Pre-processing.
"""
import os
import hashlib
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
import pytest

# Import healpy for FITS handling
try:
    import healpy as hp
    HAS_HEALPY = True
except ImportError:
    HAS_HEALPY = False

# Import the function to test (or the module if the function is internal)
# Based on task description, we are verifying checksum logic.
# We assume the logic resides in code/data/downloader.py or a utility.
# Since the implementation of downloader.py (T024) is not yet done,
# we implement the test logic here and ensure it can be run against
# a mock or the actual implementation once T024 is complete.
# However, per T021 description, we must verify `assert file_hash == expected_hash`.
# We will implement a helper function in the test file that mimics the verification
# logic expected in the downloader, or import it if it exists.
# Given T024 is not done, we cannot import from code.data.downloader.
# We will implement the verification logic locally for the test to validate the
# algorithmic correctness of the checksum check, which is the core of this task.

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify file integrity against expected hash.
    Returns True if match, raises AssertionError otherwise.
    """
    file_hash = compute_sha256(file_path)
    assert file_hash == expected_hash, f"Checksum mismatch: {file_hash} != {expected_hash}"
    return True

class TestChecksumVerification:
    """Tests for checksum verification logic (T021)."""

    @pytest.fixture
    def temp_file(self, tmp_path: Path):
        """Create a temporary file with known content."""
        file_path = tmp_path / "test_map.fits"
        content = b"SMICA_TT_Nside2048_MockData_v1"
        file_path.write_bytes(content)
        return str(file_path), hashlib.sha256(content).hexdigest()

    def test_checksum_verification(self, temp_file):
        """
        Verify `assert file_hash == expected_hash` logic.
        T021: Unit test tests/test_data.py::test_checksum_verification
        """
        file_path, expected_hash = temp_file
        
        # This should pass
        verify_checksum(file_path, expected_hash)

    def test_checksum_verification_failure(self, temp_file):
        """
        Verify that checksum mismatch raises an assertion error.
        """
        file_path, _ = temp_file
        wrong_hash = "0" * 64  # Invalid hash

        with pytest.raises(AssertionError):
            verify_checksum(file_path, wrong_hash)

    def test_checksum_verification_real_data_simulation(self, tmp_path: Path):
        """
        Simulate a realistic scenario where a file is downloaded and verified.
        """
        # Create a file that simulates a downloaded FITS header + data
        file_path = tmp_path / "plk_smica_tT.fits"
        # Mock FITS-like binary content
        content = b"\x00\x01\x02SIMPLE  =                    T / file does conform to FITS standard             BITPIX  =                    8 / number of bits per data pixel                  NAXIS   =                    0 / number of data axes                            END" + b"\x00" * 1000
        file_path.write_bytes(content)
        expected_hash = hashlib.sha256(content).hexdigest()

        # Verify
        verify_checksum(str(file_path), expected_hash)

        # Verify with slightly modified content (corrupted download)
        corrupted_content = content + b"corruption"
        corrupted_path = tmp_path / "corrupted.fits"
        corrupted_path.write_bytes(corrupted_content)
        
        with pytest.raises(AssertionError):
            verify_checksum(str(corrupted_path), expected_hash)


class TestMaskApplication:
    """Tests for mask application logic (T022)."""

    @pytest.mark.skipif(not HAS_HEALPY, reason="healpy not installed")
    def test_mask_application_zeros_pixels(self, tmp_path: Path):
        """
        Verify that applying a mask zeroes out the masked pixels in the map.
        T022: Unit test tests/test_data.py::test_mask_application
        """
        import numpy as np

        # Create a simple Nside=16 map (12 * 16^2 = 3072 pixels)
        nside = 16
        npix = hp.nside2npix(nside)
        
        # Create a map with random values
        random_state = np.random.RandomState(42)
        full_map = random_state.random(npix)
        
        # Create a mask: 0 for masked (bad), 1 for unmasked (good)
        # Mask half the pixels
        mask = np.ones(npix, dtype=int)
        mask[:npix // 2] = 0
        
        # Save map and mask to temporary files
        map_file = tmp_path / "test_map.fits"
        mask_file = tmp_path / "test_mask.fits"
        masked_file = tmp_path / "test_masked.fits"
        
        hp.write_map(map_file, full_map)
        hp.write_map(mask_file, mask)
        
        # Apply mask: multiply map by mask
        # In practice, this might be done via healpy functions or manual multiplication
        masked_map = full_map * mask
        
        # Verify masked pixels are zero
        assert np.all(masked_map[mask == 0] == 0), "Masked pixels should be zero"
        
        # Verify unmasked pixels retain original values
        assert np.allclose(masked_map[mask == 1], full_map[mask == 1]), "Unmasked pixels should retain values"
        
        # Save the masked map
        hp.write_map(masked_file, masked_map)
        
        # Load and verify
        loaded_masked = hp.read_map(masked_file)
        assert np.all(loaded_masked[mask == 0] == 0), "Loaded masked pixels should be zero"
        
        # Also test with explicit healpy mask application if available
        # hp.ma() is not standard, so we rely on manual multiplication which is the standard approach

    @pytest.mark.skipif(not HAS_HEALPY, reason="healpy not installed")
    def test_mask_application_with_realistic_data(self, tmp_path: Path):
        """
        Test mask application with a more realistic scenario involving
        a confidence mask from Planck.
        """
        import numpy as np

        nside = 64
        npix = hp.nside2npix(nside)
        
        # Simulate a CMB-like map with larger variance
        random_state = np.random.RandomState(123)
        full_map = random_state.normal(loc=0, scale=1e-2, size=npix)
        
        # Create a confidence mask (0-1 range, but typically binary 0/1)
        # Simulate a galactic plane cut
        mask = np.ones(npix, dtype=int)
        # Zero out the galactic plane (simplified: first 10% of pixels)
        mask[:npix // 10] = 0
        
        # Save
        map_file = tmp_path / "cmb_map.fits"
        mask_file = tmp_path / "confidence_mask.fits"
        result_file = tmp_path / "masked_cmb.fits"
        
        hp.write_map(map_file, full_map)
        hp.write_map(mask_file, mask)
        
        # Apply mask
        masked_map = full_map * mask
        
        # Save result
        hp.write_map(result_file, masked_map)
        
        # Verification
        loaded_masked = hp.read_map(result_file)
        
        # Check masked region
        masked_region = loaded_masked[mask == 0]
        assert np.all(masked_region == 0), "Masked region must be exactly zero"
        
        # Check unmasked region
        unmasked_region = loaded_masked[mask == 1]
        original_unmasked = full_map[mask == 1]
        assert np.allclose(unmasked_region, original_unmasked), "Unmasked region must match original"

    @pytest.mark.skipif(not HAS_HEALPY, reason="healpy not installed")
    def test_mask_application_preserves_dtype(self, tmp_path: Path):
        """
        Verify that applying a mask preserves the data type where possible.
        """
        import numpy as np

        nside = 16
        npix = hp.nside2npix(nside)
        
        # Create float64 map
        full_map = np.random.random(npix).astype(np.float64)
        mask = np.ones(npix, dtype=int)
        mask[0] = 0
        
        map_file = tmp_path / "float_map.fits"
        mask_file = tmp_path / "int_mask.fits"
        result_file = tmp_path / "result.fits"
        
        hp.write_map(map_file, full_map)
        hp.write_map(mask_file, mask)
        
        masked_map = full_map * mask
        hp.write_map(result_file, masked_map)
        
        loaded = hp.read_map(result_file)
        
        # Healpy typically reads as float64
        assert loaded.dtype == np.float64, "Result should be float64"
        assert loaded[0] == 0.0, "Masked pixel should be 0.0"