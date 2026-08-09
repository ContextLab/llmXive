"""
Tests for harmonics module.
Focus: C_l positivity and length validation and hemispherical split generation.
"""
import os
import sys
import unittest
import numpy as np
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.config import ensure_directories
from code.harmonics import compute_alm, compute_full_sky_cl, split_hemispheres
import healpy as hp

class TestClPositivityAndLength(unittest.TestCase):
    """
    Unit test for C_l positivity and length (l_max - l_min + 1) in harmonics.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup a temporary directory and a synthetic but valid map for testing.
        Note: While the project aims for real data, these unit tests require
        a deterministic, small map to verify the mathematical properties of
        the C_l calculation without downloading large files.
        """
        cls.temp_dir = tempfile.mkdtemp()
        cls.nside = 16  # Small Nside for fast testing
        cls.l_min = 2
        cls.l_max = 10
        
        # Create a simple isotropic map (all zeros + small noise)
        # This ensures the underlying physics is valid for testing the math
        np.random.seed(42)
        n_pix = hp.nside2npix(cls.nside)
        cls.test_map = np.random.normal(0, 1e-6, n_pix)
        
        # Ensure the test map is written to a FITS file if needed by downstream logic
        cls.test_map_path = os.path.join(cls.temp_dir, "test_map.fits")
        hp.write_map(cls.test_map_path, cls.test_map, overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_cl_length(self):
        """
        Test that the returned C_l array has length (l_max - l_min + 1).
        """
        # Compute alm
        alm = compute_alm(self.test_map_path, l_max=self.l_max)
        
        # Compute Cl
        cl = compute_full_sky_cl(alm, l_min=self.l_min, l_max=self.l_max)
        
        expected_length = self.l_max - self.l_min + 1
        actual_length = len(cl)
        
        self.assertEqual(
            actual_length, 
            expected_length, 
            f"C_l length {actual_length} does not match expected {expected_length} (l_max - l_min + 1)"
        )

    def test_cl_positivity(self):
        """
        Test that all C_l values are non-negative (within numerical tolerance).
        C_l represents power, so it must be >= 0.
        """
        # Compute alm
        alm = compute_alm(self.test_map_path, l_max=self.l_max)
        
        # Compute Cl
        cl = compute_full_sky_cl(alm, l_min=self.l_min, l_max=self.l_max)
        
        # Check positivity
        # Use a small tolerance for floating point errors
        tolerance = 1e-10
        for i, val in enumerate(cl):
            self.assertGreaterEqual(
                val, 
                -tolerance, 
                f"C_l at index {i} (l={self.l_min + i}) is negative: {val}"
            )

    def test_cl_values_match_healpy(self):
        """
        Regression test: Verify our manual C_l calculation matches healpy's alm2cl.
        """
        # Compute alm
        alm = compute_alm(self.test_map_path, l_max=self.l_max)
        
        # Compute Cl using our function
        cl_manual = compute_full_sky_cl(alm, l_min=self.l_min, l_max=self.l_max)
        
        # Compute Cl using healpy directly for comparison
        cl_healpy = hp.alm2cl(alm, lmax=self.l_max, lmin=self.l_min)
        
        # Check they are close
        np.testing.assert_array_almost_equal(
            cl_manual, 
            cl_healpy, 
            decimal=10, 
            err_msg="Manual C_l calculation does not match healpy's alm2cl"
        )

class TestHemisphericalSplit(unittest.TestCase):
    """
    Integration test for hemispherical split generation.
    Verifies that split_hemispheres() generates correct masks for North/South and East/West splits.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup a temporary directory and a test map.
        """
        cls.temp_dir = tempfile.mkdtemp()
        cls.nside = 16  # Small Nside for fast testing
        
        # Create a simple map with all ones (easy to verify masking)
        n_pix = hp.nside2npix(cls.nside)
        cls.test_map = np.ones(n_pix)
        
        # Ensure the test map is written to a FITS file
        cls.test_map_path = os.path.join(cls.temp_dir, "test_map.fits")
        hp.write_map(cls.test_map_path, cls.test_map, overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_hemispherical_split_shapes(self):
        """
        Test that split_hemispheres returns masks of the correct shape.
        """
        masks = split_hemispheres(self.nside)
        
        expected_shape = (hp.nside2npix(self.nside),)
        
        self.assertEqual(
            masks['north'].shape, 
            expected_shape, 
            f"North mask shape {masks['north'].shape} does not match expected {expected_shape}"
        )
        self.assertEqual(
            masks['south'].shape, 
            expected_shape, 
            f"South mask shape {masks['south'].shape} does not match expected {expected_shape}"
        )
        self.assertEqual(
            masks['east'].shape, 
            expected_shape, 
            f"East mask shape {masks['east'].shape} does not match expected {expected_shape}"
        )
        self.assertEqual(
            masks['west'].shape, 
            expected_shape, 
            f"West mask shape {masks['west'].shape} does not match expected {expected_shape}"
        )

    def test_hemispherical_split_values(self):
        """
        Test that split_hemispheres returns binary masks (0 or 1).
        """
        masks = split_hemispheres(self.nside)
        
        for name, mask in masks.items():
            unique_vals = np.unique(mask)
            self.assertTrue(
                np.array_equal(unique_vals, [0, 1]) or np.array_equal(unique_vals, [0]) or np.array_equal(unique_vals, [1]),
                f"{name} mask contains non-binary values: {unique_vals}"
            )

    def test_hemispherical_split_coverage(self):
        """
        Test that North + South and East + West masks cover the full sky.
        """
        masks = split_hemispheres(self.nside)
        
        # North + South should equal 1 everywhere (full sky coverage)
        ns_sum = masks['north'] + masks['south']
        self.assertTrue(
            np.allclose(ns_sum, 1.0),
            f"North + South masks do not cover full sky. Sum range: [{ns_sum.min()}, {ns_sum.max()}]"
        )
        
        # East + West should equal 1 everywhere (full sky coverage)
        ew_sum = masks['east'] + masks['west']
        self.assertTrue(
            np.allclose(ew_sum, 1.0),
            f"East + West masks do not cover full sky. Sum range: [{ew_sum.min()}, {ew_sum.max()}]"
        )

    def test_hemispherical_split_pixel_counts(self):
        """
        Test that hemispherical masks have approximately equal pixel counts.
        For Nside=16, total pixels = 3072. Each hemisphere should have ~1536 pixels.
        """
        masks = split_hemispheres(self.nside)
        
        total_pixels = hp.nside2npix(self.nside)
        expected_per_hemisphere = total_pixels // 2
        
        for name, mask in masks.items():
            pixel_count = np.sum(mask)
            # Allow for small rounding differences due to pixel boundaries
            tolerance = total_pixels * 0.01  # 1% tolerance
            self.assertAlmostEqual(
                pixel_count, 
                expected_per_hemisphere, 
                delta=tolerance,
                msg=f"{name} mask has {pixel_count} pixels, expected ~{expected_per_hemisphere} (tolerance: {tolerance})"
            )

    def test_hemispherical_split_with_map(self):
        """
        Integration test: Apply hemispherical masks to a test map and verify results.
        """
        masks = split_hemispheres(self.nside)
        
        # Load the test map
        test_map = hp.read_map(self.test_map_path)
        
        # Apply masks
        north_map = test_map * masks['north']
        south_map = test_map * masks['south']
        east_map = test_map * masks['east']
        west_map = test_map * masks['west']
        
        # Verify that masked values are zero
        self.assertTrue(
            np.all(north_map[masks['south'] == 1] == 0),
            "North map has non-zero values in South region"
        )
        self.assertTrue(
            np.all(south_map[masks['north'] == 1] == 0),
            "South map has non-zero values in North region"
        )
        self.assertTrue(
            np.all(east_map[masks['west'] == 1] == 0),
            "East map has non-zero values in West region"
        )
        self.assertTrue(
            np.all(west_map[masks['east'] == 1] == 0),
            "West map has non-zero values in East region"
        )

if __name__ == '__main__':
    unittest.main()