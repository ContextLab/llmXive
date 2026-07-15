"""
Unit tests for statistical analysis functions.

This test suite validates the statistical analysis module (code/analysis/stats.py)
by feeding synthetic accuracy data into anova_test and verifying the output structure.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestStatisticalAnalysis(unittest.TestCase):
    """Tests for statistical analysis functions."""

    def test_anova_test_returns_expected_keys(self):
        """
        Test that anova_test returns a dictionary containing 'f_statistic' and 'p_value'.
        
        This test feeds synthetic accuracy data into stats.anova_test and checks
        that the returned object contains the required keys.
        """
        # Import the stats module (assuming it exists or will be created by T030)
        # We use a mock import in case the module isn't fully implemented yet,
        # but the task requires us to test the real function.
        from code.analysis import stats

        # Create synthetic accuracy data for three model groups
        # Format: Dict[str, List[float]]
        synthetic_data = {
            "high_entropy_model": [0.85, 0.88, 0.82, 0.90, 0.87],
            "low_entropy_model": [0.75, 0.78, 0.72, 0.80, 0.77],
            "target_model": [0.80, 0.83, 0.79, 0.85, 0.82]
        }

        # Call the anova_test function
        # Note: This assumes stats.anova_test is implemented as per T030
        try:
            result = stats.anova_test(synthetic_data)
        except AttributeError:
            # If the function doesn't exist yet, we fail the test explicitly
            self.fail("stats.anova_test function is not implemented yet")
        except Exception as e:
            self.fail(f"stats.anova_test raised an unexpected exception: {e}")

        # Verify the result is a dictionary
        self.assertIsInstance(result, dict, "anova_test should return a dictionary")

        # Verify the required keys are present
        self.assertIn("f_statistic", result, "Result must contain 'f_statistic'")
        self.assertIn("p_value", result, "Result must contain 'p_value'")

        # Verify the types of the values
        self.assertIsInstance(result["f_statistic"], (int, float), "f_statistic must be numeric")
        self.assertIsInstance(result["p_value"], (int, float), "p_value must be numeric")

        # Additional sanity checks
        self.assertGreaterEqual(result["f_statistic"], 0, "f_statistic must be non-negative")
        self.assertGreaterEqual(result["p_value"], 0, "p_value must be non-negative")
        self.assertLessEqual(result["p_value"], 1, "p_value must be <= 1")

    def test_anova_test_with_empty_groups(self):
        """Test behavior with empty data groups (edge case)."""
        from code.analysis import stats

        # Empty data should raise an error or return None, depending on implementation
        # For this test, we expect it to handle gracefully or raise a clear error
        synthetic_data = {
            "group1": [],
            "group2": [],
            "group3": []
        }

        # We expect this to raise a ValueError or similar, not crash silently
        with self.assertRaises((ValueError, IndexError, ZeroDivisionError)):
            stats.anova_test(synthetic_data)

    def test_anova_test_with_single_group(self):
        """Test behavior with only one group (ANOVA requires at least 2)."""
        from code.analysis import stats

        synthetic_data = {
            "only_group": [0.85, 0.88, 0.82]
        }

        # ANOVA requires at least 2 groups
        with self.assertRaises((ValueError, IndexError)):
            stats.anova_test(synthetic_data)

    def test_anova_test_with_two_groups(self):
        """Test ANOVA with exactly two groups (should work, though t-test is more common)."""
        from code.analysis import stats

        synthetic_data = {
            "group_a": [0.85, 0.88, 0.82],
            "group_b": [0.75, 0.78, 0.72]
        }

        result = stats.anova_test(synthetic_data)
        
        self.assertIn("f_statistic", result)
        self.assertIn("p_value", result)

    def test_pairwise_t_test_structure(self):
        """Test that pairwise_t_test returns expected structure (if implemented)."""
        from code.analysis import stats

        # Check if pairwise_t_test exists
        if not hasattr(stats, 'pairwise_t_test'):
            self.skipTest("pairwise_t_test not yet implemented")

        synthetic_data = {
            "model_a": [0.85, 0.88, 0.82],
            "model_b": [0.75, 0.78, 0.72],
            "model_c": [0.80, 0.83, 0.79]
        }

        result = stats.pairwise_t_test(synthetic_data)
        
        self.assertIsInstance(result, dict)
        # Should contain pairwise comparisons
        self.assertIn("comparisons", result)
        self.assertIsInstance(result["comparisons"], list)


if __name__ == "__main__":
    unittest.main()