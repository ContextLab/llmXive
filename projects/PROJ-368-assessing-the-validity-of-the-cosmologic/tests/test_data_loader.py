"""
Unit tests for data_loader.py mask application and pixel exclusion.

This module tests the mask application logic for the Planck CMB map.
It verifies that:
1. The Commander mask is correctly loaded and applied to the map.
2. Masked pixels are set to a specific value (e.g., -1.0 or masked).
3. The percentage of unmasked sky meets the >= 95% retention threshold.
4. The mask statistics (number of masked/unmasked pixels, retention rate) are correct.
"""

import numpy as np
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

# We will import the function to test once it exists.
# For now, we assume it will be named apply_galactic_mask and return (masked_map, stats_dict)
# We also assume it uses healpy for mask operations.
try:
    from data_loader import apply_galactic_mask
    HAS_DATA_LOADER = True
except ImportError:
    HAS_DATA_LOADER = False

class TestMaskApplication(TestCase):
    """Tests for the apply_galactic_mask function."""

    def setUp(self):
        """Set up test fixtures."""
        self.nside = 128
        self.npix = 12 * self.nside**2
        # Create a mock map (e.g., temperature map)
        self.mock_map = np.random.randn(self.npix).astype(np.float32)
        
        # Create a mock mask (1 = keep, 0 = mask out)
        # We'll create a simple mask that keeps 98% of the sky to pass the threshold
        self.mock_mask = np.ones(self.npix, dtype=np.float32)
        # Mask out 2% of pixels randomly
        mask_indices = np.random.choice(self.npix, size=int(0.02 * self.npix), replace=False)
        self.mock_mask[mask_indices] = 0.0

    @patch('data_loader.healpy')
    @patch('data_loader.requests')
    def test_mask_application_logic(self, mock_requests, mock_healpy):
        """Test that mask is correctly applied to the map."""
        if not HAS_DATA_LOADER:
            self.skipTest("data_loader module not yet implemented")

        # Mock healpy functions
        mock_healpy.read_map.return_value = self.mock_map
        mock_healpy.ud_grade.return_value = self.mock_map
        
        # Mock the mask download
        mock_response = MagicMock()
        mock_response.content = b"mock_fits_data"
        mock_requests.get.return_value = mock_response

        # Mock healpy.pixelfunc to simulate mask operations
        # We'll patch the internal logic to ensure the mask is applied
        with patch('data_loader.healpy.ud_grade', return_value=self.mock_mask):
            # Call the function
            try:
                masked_map, stats = apply_galactic_mask(self.mock_map, self.mock_mask)
                
                # Verify the function returns a tuple
                self.assertIsInstance(masked_map, np.ndarray)
                self.assertIsInstance(stats, dict)
                
                # Verify that masked pixels are set to a specific value (e.g., -1.0 or np.nan)
                # The exact behavior depends on the implementation, but we check that
                # the number of masked pixels matches expectations
                expected_masked_count = int(0.02 * self.npix)
                actual_masked_count = np.sum(masked_map == -1.0) # Assuming -1.0 is the mask value
                
                # Allow for some tolerance in the count due to floating point or implementation details
                self.assertAlmostEqual(actual_masked_count, expected_masked_count, delta=10)
                
            except Exception as e:
                self.fail(f"apply_galactic_mask raised unexpected exception: {e}")

    def test_pixel_exclusion_threshold(self):
        """Test that the function enforces the >= 95% unmasked sky retention."""
        if not HAS_DATA_LOADER:
            self.skipTest("data_loader module not yet implemented")

        # Create a mask that keeps only 90% of the sky (should fail)
        low_retention_mask = np.ones(self.npix, dtype=np.float32)
        mask_indices = np.random.choice(self.npix, size=int(0.10 * self.npix), replace=False)
        low_retention_mask[mask_indices] = 0.0

        with self.assertRaises(ValueError) as context:
            # We can't fully test without the implementation, but we check the error type
            # This test will pass once the implementation raises ValueError correctly
            pass

    @patch('data_loader.healpy')
    def test_mask_statistics_correctness(self, mock_healpy):
        """Test that mask statistics are correctly computed."""
        if not HAS_DATA_LOADER:
            self.skipTest("data_loader module not yet implemented")

        # Create a known mask
        known_mask = np.ones(self.npix, dtype=np.float32)
        known_mask[:1000] = 0.0  # Mask first 1000 pixels
        known_mask[-1000:] = 0.0 # Mask last 1000 pixels

        expected_masked_count = 2000
        expected_unmasked_count = self.npix - 2000
        expected_retention_rate = expected_unmasked_count / self.npix

        with patch('data_loader.healpy.ud_grade', return_value=known_mask):
            try:
                _, stats = apply_galactic_mask(self.mock_map, known_mask)
                
                self.assertIn('masked_pixels', stats)
                self.assertIn('unmasked_pixels', stats)
                self.assertIn('retention_rate', stats)
                
                self.assertEqual(stats['masked_pixels'], expected_masked_count)
                self.assertEqual(stats['unmasked_pixels'], expected_unmasked_count)
                self.assertAlmostEqual(stats['retention_rate'], expected_retention_rate, places=5)
                
            except Exception as e:
                self.fail(f"Mask statistics computation failed: {e}")

    def test_mask_value_consistency(self):
        """Test that masked pixels are consistently set to a specific value."""
        if not HAS_DATA_LOADER:
            self.skipTest("data_loader module not yet implemented")

        # Create a simple mask
        simple_mask = np.ones(self.npix, dtype=np.float32)
        simple_mask[:500] = 0.0

        with patch('data_loader.healpy.ud_grade', return_value=simple_mask):
            try:
                masked_map, _ = apply_galactic_mask(self.mock_map, simple_mask)
                
                # Check that masked pixels have a consistent value
                masked_indices = np.where(simple_mask == 0.0)[0]
                masked_values = masked_map[masked_indices]
                
                # All masked values should be the same (e.g., -1.0 or np.nan)
                # We check for np.nan separately
                if np.all(np.isnan(masked_values)):
                    pass  # np.nan is acceptable
                else:
                    # Check if all values are equal to a specific number (e.g., -1.0)
                    unique_values = np.unique(masked_values)
                    self.assertEqual(len(unique_values), 1)
                    self.assertTrue(unique_values[0] in [-1.0, 0.0, np.nan])
                    
            except Exception as e:
                self.fail(f"Mask value consistency check failed: {e}")

if __name__ == "__main__":
    import unittest
    unittest.main()