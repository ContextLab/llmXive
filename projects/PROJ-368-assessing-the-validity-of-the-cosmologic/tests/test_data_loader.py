import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import healpy as hp

# Import the function under test from the project module
from data_loader import downgrade_resolution
from config import ensure_directories, PROCESSED_MAP_FILENAME

class TestDowngradeResolution:
    """
    Unit tests for the Nside downgrade memory usage and NaN checks.
    Corresponds to Task T013.
    """

    def test_downgrade_no_nan_inf(self):
        """
        Verify that the downgrade process does not introduce NaN or Inf values.
        """
        # Setup: Create a temporary directory for test artifacts
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock high-resolution map (Nside=2048) with random Gaussian values
            # This simulates the output of apply_galactic_mask (before actual download)
            nside_in = 2048
            nside_out = 128
            npix_in = hp.nside2npix(nside_in)
            
            # Generate realistic CMB-like random data (mean=0, std=1e-5)
            mock_map = np.random.normal(0.0, 1e-5, npix_in).astype(np.float32)
            
            # Inject a known valid value to ensure we aren't just testing empty arrays
            mock_map[0] = 1.0

            input_path = os.path.join(tmpdir, "test_input_n2048.fits")
            output_path = os.path.join(tmpdir, "test_output_n128.fits")

            # Save the mock high-res map
            hp.write_map(input_path, mock_map, overwrite=True)

            # Execute the downgrade
            try:
                downgrade_resolution(input_path, output_path, nside_out)
            except Exception as e:
                pytest.fail(f"downgrade_resolution raised an unexpected exception: {e}")

            # Verification 1: Check if output file exists
            assert os.path.exists(output_path), "Output FITS file was not created."

            # Verification 2: Load the output and check for NaN/Inf
            output_map = hp.read_map(output_path)
            
            assert not np.any(np.isnan(output_map)), "Downgraded map contains NaN values."
            assert not np.any(np.isinf(output_map)), "Downgraded map contains Inf values."
            
            # Verification 3: Check shape matches expected Nside=128
            expected_npix = hp.nside2npix(nside_out)
            assert output_map.shape[0] == expected_npix, f"Output shape {output_map.shape[0]} != expected {expected_npix}"

    def test_downgrade_memory_footprint(self):
        """
        Verify that the downgraded map fits within the expected memory constraints.
        The task requires the Nside=128 map to fit in <100MB RAM.
        Nside=128 -> 49152 pixels. 
        Float64: 49152 * 8 bytes ≈ 393 KB.
        Float32: 49152 * 4 bytes ≈ 196 KB.
        Even with FITS overhead, this is well under 100MB.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            nside_in = 2048
            nside_out = 128
            npix_in = hp.nside2npix(nside_in)
            
            # Create a large mock map to simulate memory pressure during processing
            # We create it in float64 to be conservative
            mock_map = np.random.random(npix_in).astype(np.float64)
            
            input_path = os.path.join(tmpdir, "mem_test_in.fits")
            output_path = os.path.join(tmpdir, "mem_test_out.fits")

            hp.write_map(input_path, mock_map, overwrite=True)

            # Run downgrade
            downgrade_resolution(input_path, output_path, nside_out)

            # Load and estimate size
            output_map = hp.read_map(output_path)
            
            # Calculate approximate memory usage in bytes
            # Assuming the map is loaded into memory as a numpy array (float64 by default in healpy read)
            memory_usage_bytes = output_map.nbytes
            
            limit_bytes = 100 * 1024 * 1024  # 100 MB

            assert memory_usage_bytes < limit_bytes, (
                f"Downgraded map memory usage ({memory_usage_bytes / 1024 / 1024:.2f} MB) "
                f"exceeds the 100 MB limit."
            )

    def test_downgrade_preserves_signal_mean(self):
        """
        Verify that the downgraded map preserves the mean signal (within tolerance).
        Downgrading averages pixels, so the mean should remain statistically similar
        for a zero-mean field, or exactly preserved for a constant field.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            nside_in = 2048
            nside_out = 128
            
            # Create a map with a known non-zero mean to test preservation
            base_mean = 5.0e-6  # Typical CMB temperature fluctuation scale
            npix_in = hp.nside2npix(nside_in)
            
            # Create a map that is mostly constant + noise
            mock_map = np.full(npix_in, base_mean, dtype=np.float64)
            mock_map += np.random.normal(0, 1e-7, npix_in)
            
            input_path = os.path.join(tmpdir, "mean_test_in.fits")
            output_path = os.path.join(tmpdir, "mean_test_out.fits")

            hp.write_map(input_path, mock_map, overwrite=True)

            downgrade_resolution(input_path, output_path, nside_out)

            output_map = hp.read_map(output_path)
            
            original_mean = np.mean(mock_map)
            downgraded_mean = np.mean(output_map)
            
            # Tolerance: The downgraded mean should be very close to the original mean
            # Allow for slight numerical differences in the smoothing/downgrade algorithm
            tolerance = 1e-10
            
            assert np.abs(original_mean - downgraded_mean) < tolerance, (
                f"Mean signal not preserved: Original={original_mean}, Downgraded={downgraded_mean}"
            )