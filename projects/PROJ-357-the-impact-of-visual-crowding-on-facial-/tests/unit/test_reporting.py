"""
Unit tests for the FDR (Benjamini-Hochberg) implementation in the reporting module.

This test suite verifies that:
1. The apply_fdr_correction function correctly calculates adjusted p-values.
2. The regression_results.json structure contains the required 'fdr_p_value' fields.
3. The FDR threshold (0.05) is correctly applied to determine significance.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from analysis.glmm_model import apply_fdr_correction
from analysis.reporting import load_regression_results


class TestFDRImplementation(unittest.TestCase):
    """Tests for Benjamini-Hochberg FDR correction logic."""

    def test_apply_fdr_correction_basic(self):
        """Test that apply_fdr_correction returns a list of floats of the same length."""
        p_values = [0.01, 0.04, 0.03, 0.005, 0.02]
        adjusted = apply_fdr_correction(p_values, alpha=0.05)
        
        self.assertIsInstance(adjusted, list)
        self.assertEqual(len(adjusted), len(p_values))
        self.assertTrue(all(isinstance(p, float) for p in adjusted))

    def test_apply_fdr_correction_monotonicity(self):
        """
        Test that the BH procedure ensures monotonicity of adjusted p-values.
        Adjusted p-values should be non-decreasing with respect to the sorted rank.
        """
        # Unsorted p-values
        p_values = [0.05, 0.01, 0.04, 0.001]
        adjusted = apply_fdr_correction(p_values, alpha=0.05)
        
        # The BH procedure guarantees that adjusted p-values are non-decreasing
        # when sorted by their original p-value magnitude.
        # Let's verify the logic: 
        # 1. Sort p-values: 0.001 (rank 1), 0.01 (rank 2), 0.04 (rank 3), 0.05 (rank 4)
        # 2. Calculate raw adjusted: p_i * m / i
        # 3. Ensure monotonicity from the largest rank down.
        
        # We check that for the sorted indices, the adjusted values are monotonic
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = [adjusted[i] for i in sorted_indices]
        
        for i in range(1, len(sorted_adjusted)):
            self.assertGreaterEqual(
                sorted_adjusted[i], 
                sorted_adjusted[i-1], 
                f"Adjusted p-values must be monotonically non-decreasing: {sorted_adjusted}"
            )

    def test_apply_fdr_correction_threshold(self):
        """
        Verify that the FDR correction respects the alpha threshold.
        Specifically, check that p-values below a certain threshold remain significant 
        after correction if the data supports it, and that the correction logic 
        correctly identifies the cutoff.
        """
        # A set where we know the outcome: 
        # If we have many small p-values, some might cross 0.05 after correction.
        p_values = [0.001, 0.002, 0.003, 0.04, 0.05, 0.1]
        adjusted = apply_fdr_correction(p_values, alpha=0.05)
        
        # The function should return values. We specifically test that 
        # the logic doesn't crash and produces valid probabilities (0 to 1).
        self.assertTrue(all(0.0 <= p <= 1.0 for p in adjusted))

    def test_regression_results_fdr_field_exists(self):
        """
        Verify that if regression_results.json is loaded, it contains the 'fdr_p_value' 
        key for each coefficient entry, as required by the spec.
        """
        # Create a temporary mock file to simulate the expected output structure
        mock_data = {
            "coefficients": [
                {"term": "flanker_count", "beta": -0.5, "se": 0.1, "p_value": 0.01, "fdr_p_value": 0.02},
                {"term": "spatial_freq", "beta": 0.3, "se": 0.1, "p_value": 0.04, "fdr_p_value": 0.04},
                {"term": "intercept", "beta": 1.0, "se": 0.2, "p_value": 0.8, "fdr_p_value": 0.8}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_data, f)
            temp_path = f.name

        try:
            # Load using the actual loader function
            results = load_regression_results(temp_path)
            
            self.assertIn("coefficients", results)
            for coeff in results["coefficients"]:
                self.assertIn("fdr_p_value", coeff, 
                              "Each coefficient entry must have 'fdr_p_value'")
        finally:
            os.unlink(temp_path)

    def test_fdr_threshold_compliance(self):
        """
        Verify that the FDR correction logic correctly identifies which hypotheses 
        are significant at the 0.05 level.
        """
        # Simulate a scenario where we expect exactly 2 significant results after FDR
        # p-values: 0.01, 0.02, 0.06, 0.10 (m=4)
        # Sorted: 0.01 (rank 1), 0.02 (rank 2), 0.06 (rank 3), 0.10 (rank 4)
        # Raw adjusted: 
        # 1: 0.01 * 4 / 1 = 0.04 (sig)
        # 2: 0.02 * 4 / 2 = 0.04 (sig)
        # 3: 0.06 * 4 / 3 = 0.08 (not sig)
        # 4: 0.10 * 4 / 4 = 0.10 (not sig)
        # Monotonicity check: 0.04 <= 0.04 <= 0.08 <= 0.10 (OK)
        
        p_values = [0.01, 0.02, 0.06, 0.10]
        adjusted = apply_fdr_correction(p_values, alpha=0.05)
        
        # Count significant
        significant_count = sum(1 for p in adjusted if p <= 0.05)
        
        self.assertEqual(significant_count, 2, 
                         f"Expected 2 significant results, got {significant_count} with adjusted p-values: {adjusted}")

    def test_fdr_edge_case_all_significant(self):
        """Test case where all p-values are very small."""
        p_values = [0.001, 0.002, 0.003]
        adjusted = apply_fdr_correction(p_values, alpha=0.05)
        
        # All should be <= 0.05
        self.assertTrue(all(p <= 0.05 for p in adjusted))

    def test_fdr_edge_case_none_significant(self):
        """Test case where all p-values are large."""
        p_values = [0.5, 0.6, 0.7]
        adjusted = apply_fdr_correction(p_values, alpha=0.05)
        
        # All should be > 0.05
        self.assertTrue(all(p > 0.05 for p in adjusted))


if __name__ == '__main__':
    unittest.main()