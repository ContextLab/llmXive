import os
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_loader import downgrade_resolution, load_planck_map
from config import ensure_directories

class TestNsideDowngrade(unittest.TestCase):
    """
    Unit test for Nside downgrade memory usage and NaN checks.
    This test verifies that:
    1. The downgrade operation from Nside=2048 to Nside=128 completes successfully.
    2. The resulting map fits within memory constraints (simulated via size check).
    3. The resulting map contains no NaN or Inf values.
    4. The output file is written correctly.
    """

    def setUp(self):
        """
        Set up test fixtures.
        Since we cannot download the full 2GB Planck map in this unit test environment,
        we create a synthetic valid FITS file mimicking the structure of the Planck map
        to test the logic of `downgrade_resolution` and the integrity checks.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.nside_high = 2048
        self.nside_low = 128
        
        # Calculate expected number of pixels
        # Npix = 12 * Nside^2
        self.npix_high = 12 * (self.nside_high ** 2)
        self.npix_low = 12 * (self.nside_low ** 2)
        
        # Create a mock map file (simulating the masked Nside=2048 map)
        # We use a simple pattern to ensure it's valid data
        mock_map = np.random.randn(self.npix_high).astype(np.float32)
        
        # Inject a few NaNs to simulate bad pixels that should ideally be handled or checked
        # However, the requirement is to check that the *output* has no NaNs.
        # The downgrade function itself (via healpy) usually handles interpolation.
        # We will create a clean map for the test to ensure the pipeline works.
        mock_map_clean = np.random.randn(self.npix_high).astype(np.float32)
        
        self.input_path = os.path.join(self.temp_dir, "mock_masked_n2048.fits")
        self.output_path = os.path.join(self.temp_dir, "mock_downgraded_n128.fits")
        
        # Write mock FITS file using healpy if available, otherwise use astropy
        try:
            import healpy as hp
            hp.write_map(self.input_path, mock_map_clean, overwrite=True)
            self.use_healpy = True
        except ImportError:
            # Fallback to astropy if healpy is not installed in test env
            from astropy.io import fits
            hdu = fits.PrimaryHDU(data=mock_map_clean)
            hdu.header['NSIDE'] = self.nside_high
            hdu.writeto(self.input_path, overwrite=True)
            self.use_healpy = False

    def test_downgrade_no_nan_inf(self):
        """
        Verify that the downgraded map contains no NaN or Inf values.
        """
        # Run the downgrade
        if self.use_healpy:
            # If healpy is available, we can test the actual function
            # We need to ensure the function handles the file path correctly
            result_map = downgrade_resolution(self.input_path, self.output_path)
            
            # Check for NaN and Inf
            self.assertFalse(np.any(np.isnan(result_map)), "Downgraded map contains NaN values")
            self.assertFalse(np.any(np.isinf(result_map)), "Downgraded map contains Inf values")
            
            # Verify file was written
            self.assertTrue(os.path.exists(self.output_path), "Output file was not created")
        else:
            # If healpy is not available, we simulate the check logic
            # This path ensures the test structure exists even if dependencies are missing
            # In a real CI, healpy should be present.
            self.skipTest("healpy not installed, skipping functional downgrade test")

    def test_downgrade_memory_footprint(self):
        """
        Verify that the downgraded map size is consistent with Nside=128.
        Nside=128 has 12 * 128^2 = 196,608 pixels.
        As float32, this is approx 196,608 * 4 bytes = ~786 KB.
        This is well within the <100MB RAM constraint.
        """
        if self.use_healpy:
            if not os.path.exists(self.output_path):
                # Run downgrade first if not already done
                downgrade_resolution(self.input_path, self.output_path)
            
            import healpy as hp
            loaded_map = hp.read_map(self.output_path)
            
            expected_npix = 12 * (self.nside_low ** 2)
            self.assertEqual(len(loaded_map), expected_npix, 
                             f"Pixel count mismatch: expected {expected_npix}, got {len(loaded_map)}")
            
            # Check size in bytes
            size_bytes = loaded_map.nbytes
            max_allowed_bytes = 100 * 1024 * 1024 # 100 MB
            self.assertLess(size_bytes, max_allowed_bytes, 
                            f"Map size {size_bytes} bytes exceeds 100MB limit")
        else:
            self.skipTest("healpy not installed, skipping memory footprint test")

    def test_downgrade_preserves_structure(self):
        """
        Verify that the downgraded map is not empty and has reasonable statistics.
        """
        if self.use_healpy:
            if not os.path.exists(self.output_path):
                downgrade_resolution(self.input_path, self.output_path)
            
            import healpy as hp
            loaded_map = hp.read_map(self.output_path)
            
            # Check that mean and std are finite
            self.assertTrue(np.isfinite(np.mean(loaded_map)), "Mean is not finite")
            self.assertTrue(np.isfinite(np.std(loaded_map)), "Std is not finite")
            
            # Check that variance is non-zero (since input was random)
            self.assertGreater(np.var(loaded_map), 0, "Variance is zero, map might be empty")
        else:
            self.skipTest("healpy not installed, skipping structure test")

if __name__ == "__main__":
    unittest.main()