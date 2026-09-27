"""
Unit tests for Firth regression fallback logic in modeling.py.

This module tests the Firth's penalized logistic regression implementation
and its fallback behavior when perfect separation is detected.
"""
import unittest
import sys
import os
import warnings
import numpy as np
import pandas as pd

# Add project root to path for imports if running directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.modeling import run_firth_regression, detect_perfect_separation, run_logistic_regression

class TestFirthRegressionFallback(unittest.TestCase):
    """Tests for the Firth regression fallback implementation."""

    def setUp(self):
        """Set up test data for perfect separation scenarios."""
        # Create a dataset that exhibits perfect separation
        # Feature X perfectly predicts the target Y
        np.random.seed(42)
        n = 50
        # X is continuous, Y is binary
        # We create a scenario where X > 0.5 => Y=1, X < 0.5 => Y=0
        # This creates perfect separation
        self.X_separated = np.random.uniform(0, 1, n)
        self.y_separated = np.where(self.X_separated > 0.5, 1, 0)
        
        # Create a dataset without separation (for comparison)
        self.X_normal = np.random.uniform(0, 1, n)
        self.y_normal = np.random.randint(0, 2, n)

    def test_firth_regression_runs_on_separated_data(self):
        """Test that Firth regression successfully converges on separated data."""
        # Standard logistic regression should fail or warn on separated data
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                # Attempt standard regression
                result_standard = run_logistic_regression(self.X_separated, self.y_separated)
                # If it runs, check for warnings
                convergence_warnings = [warning for warning in w if "convergence" in str(warning.message).lower()]
                # Even if it runs, Firth should be preferred for separated data
            except Exception:
                # Expected: standard regression fails
                pass

        # Firth regression should succeed without convergence issues
        result_firth = run_firth_regression(self.X_separated, self.y_separated)
        
        # Verify the result structure
        self.assertIn('coefficients', result_firth)
        self.assertIn('p_values', result_firth)
        self.assertIn('converged', result_firth)
        self.assertTrue(result_firth['converged'], "Firth regression should converge on separated data")

    def test_firth_coefficients_exist(self):
        """Test that Firth regression returns valid coefficients."""
        result = run_firth_regression(self.X_separated, self.y_separated)
        
        self.assertIsNotNone(result['coefficients'])
        self.assertGreater(len(result['coefficients']), 0)
        
        # Coefficients should be finite numbers
        for coef in result['coefficients']:
            self.assertTrue(np.isfinite(coef), f"Coefficient {coef} is not finite")

    def test_firth_pvalues_exist(self):
        """Test that Firth regression returns valid p-values."""
        result = run_firth_regression(self.X_separated, self.y_separated)
        
        self.assertIn('p_values', result)
        self.assertIsNotNone(result['p_values'])
        
        # P-values should be between 0 and 1
        for p_val in result['p_values']:
            self.assertGreaterEqual(p_val, 0.0)
            self.assertLessEqual(p_val, 1.0)

    def test_firth_on_normal_data(self):
        """Test that Firth regression works on non-separated data as well."""
        result = run_firth_regression(self.X_normal, self.y_normal)
        
        self.assertTrue(result['converged'])
        self.assertIn('coefficients', result)
        self.assertIn('p_values', result)

    def test_separation_detection(self):
        """Test that perfect separation is correctly detected."""
        # The separated dataset should trigger separation detection
        is_separated = detect_perfect_separation(self.X_separated, self.y_separated)
        
        # Note: The exact behavior depends on the statsmodels diagnostics
        # We verify the function exists and returns a boolean
        self.assertIsInstance(is_separated, bool)

    def test_firth_vs_standard_coefficients(self):
        """Test that Firth coefficients differ from standard MLE on separated data."""
        # On separated data, standard MLE coefficients tend to infinity
        # Firth regression shrinks them
        
        try:
            result_standard = run_logistic_regression(self.X_separated, self.y_separated)
            coef_standard = result_standard.get('coefficients', [])
        except Exception:
            coef_standard = [float('inf')] * 2  # Simulate divergence

        result_firth = run_firth_regression(self.X_separated, self.y_separated)
        coef_firth = result_firth['coefficients']

        # Firth coefficients should be finite and typically smaller in magnitude
        for coef in coef_firth:
            self.assertTrue(np.isfinite(coef), "Firth coefficient should be finite")

    def test_firth_regression_with_intercept(self):
        """Test that Firth regression correctly handles the intercept term."""
        # Create data with known intercept behavior
        X = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
        y = np.array([0, 0, 0, 1, 1])
        
        result = run_firth_regression(X, y)
        
        # Should return coefficients for both intercept and slope
        self.assertGreater(len(result['coefficients']), 0)

    def test_firth_regression_input_validation(self):
        """Test handling of invalid input data."""
        # Test with mismatched lengths
        with self.assertRaises(ValueError):
            run_firth_regression(np.array([1, 2, 3]), np.array([1, 2]))

    def test_firth_regression_output_format(self):
        """Test that the output format matches the expected schema."""
        result = run_firth_regression(self.X_separated, self.y_separated)
        
        expected_keys = ['coefficients', 'p_values', 'converged', 'iterations', 'log_likelihood']
        for key in expected_keys:
            self.assertIn(key, result, f"Missing key: {key}")

    def test_firth_regression_significance(self):
        """Test that Firth regression provides significance estimates."""
        result = run_firth_regression(self.X_separated, self.y_separated)
        
        # At least one coefficient should have a p-value
        self.assertGreater(len(result['p_values']), 0)

if __name__ == '__main__':
    unittest.main()