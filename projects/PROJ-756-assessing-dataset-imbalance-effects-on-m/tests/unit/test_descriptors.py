"""
Unit tests for Magpie descriptor computation in code/descriptors.py.

These tests verify that:
1. The descriptor computation logic handles valid chemical formulas correctly.
2. The L2 normalization is applied as expected.
3. Edge cases (empty formulas, invalid elements) are handled gracefully.
4. The output shape and data types match the specification (14 descriptors).
"""
import unittest
import numpy as np
import sys
import os

# Add the code directory to the path so we can import descriptors
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from descriptors import compute_magpie_descriptors, normalize_l2, compute_composition_vector


class TestMagpieDescriptors(unittest.TestCase):
    """Test cases for Magpie descriptor computation functions."""

    def test_compute_composition_vector_valid_formula(self):
        """Test that a valid chemical formula produces the correct composition vector."""
        formula = "H2O"
        vector = compute_composition_vector(formula)
        
        # H2O should have 2 H and 1 O, total 3 atoms
        # H index should be ~2/3, O index ~1/3
        self.assertIsInstance(vector, np.ndarray)
        self.assertEqual(vector.shape, (14,))
        # Check that sum is close to 1 (normalized composition)
        self.assertAlmostEqual(np.sum(vector), 1.0, places=5)

    def test_compute_composition_vector_complex_formula(self):
        """Test a more complex formula like Fe2O3."""
        formula = "Fe2O3"
        vector = compute_composition_vector(formula)
        
        self.assertIsInstance(vector, np.ndarray)
        self.assertEqual(vector.shape, (14,))
        # Fe2O3: 2 Fe, 3 O -> total 5 atoms
        # Fe should be 0.4, O should be 0.6
        self.assertAlmostEqual(np.sum(vector), 1.0, places=5)

    def test_compute_composition_vector_empty_formula(self):
        """Test that an empty formula raises a ValueError."""
        with self.assertRaises(ValueError):
            compute_composition_vector("")

    def test_compute_composition_vector_invalid_element(self):
        """Test that an invalid element raises a ValueError."""
        # "X" is not a valid chemical element in our context
        with self.assertRaises(ValueError):
            compute_composition_vector("X2O")

    def test_normalize_l2_single_vector(self):
        """Test L2 normalization on a single vector."""
        vector = np.array([3.0, 4.0])
        normalized = normalize_l2(vector)
        
        # L2 norm of [3, 4] is 5
        # Normalized should be [0.6, 0.8]
        self.assertAlmostEqual(np.linalg.norm(normalized), 1.0, places=5)
        self.assertAlmostEqual(normalized[0], 0.6, places=5)
        self.assertAlmostEqual(normalized[1], 0.8, places=5)

    def test_normalize_l2_zero_vector(self):
        """Test that L2 normalization on a zero vector raises a ValueError."""
        vector = np.array([0.0, 0.0])
        with self.assertRaises(ValueError):
            normalize_l2(vector)

    def test_compute_magpie_descriptors_valid_formula(self):
        """Test that compute_magpie_descriptors returns the correct shape for a valid formula."""
        formula = "SiO2"
        descriptors = compute_magpie_descriptors(formula)
        
        self.assertIsInstance(descriptors, np.ndarray)
        self.assertEqual(descriptors.shape, (14,))
        # Check that all values are finite
        self.assertTrue(np.all(np.isfinite(descriptors)))

    def test_compute_magpie_descriptors_multiple_elements(self):
        """Test with a formula containing multiple elements."""
        formula = "NaCl"
        descriptors = compute_magpie_descriptors(formula)
        
        self.assertIsInstance(descriptors, np.ndarray)
        self.assertEqual(descriptors.shape, (14,))
        self.assertTrue(np.all(np.isfinite(descriptors)))

    def test_compute_magpie_descriptors_empty_formula(self):
        """Test that an empty formula raises a ValueError."""
        with self.assertRaises(ValueError):
            compute_magpie_descriptors("")

    def test_compute_magpie_descriptors_invalid_element(self):
        """Test that an invalid element raises a ValueError."""
        with self.assertRaises(ValueError):
            compute_magpie_descriptors("InvalidElement")

    def test_compute_magpie_descriptors_numeric_values(self):
        """Test that the computed descriptors are numeric and reasonable."""
        formula = "Fe2O3"
        descriptors = compute_magpie_descriptors(formula)
        
        # Check that descriptors are not all zeros (unless the formula is degenerate)
        # For Fe2O3, we expect non-zero descriptors
        self.assertNotEqual(np.sum(np.abs(descriptors)), 0.0)
        
        # Check that the values are within a reasonable range (e.g., not 1e10)
        self.assertTrue(np.all(np.abs(descriptors) < 1e6))

    def test_compute_magpie_descriptors_consistency(self):
        """Test that the same formula produces the same descriptors."""
        formula = "H2O"
        descriptors1 = compute_magpie_descriptors(formula)
        descriptors2 = compute_magpie_descriptors(formula)
        
        np.testing.assert_array_almost_equal(descriptors1, descriptors2)

    def test_compute_magpie_descriptors_case_insensitivity(self):
        """Test that element symbols are case-insensitive."""
        formula1 = "H2O"
        formula2 = "h2o"
        
        descriptors1 = compute_magpie_descriptors(formula1)
        descriptors2 = compute_magpie_descriptors(formula2)
        
        np.testing.assert_array_almost_equal(descriptors1, descriptors2)

if __name__ == "__main__":
    unittest.main()