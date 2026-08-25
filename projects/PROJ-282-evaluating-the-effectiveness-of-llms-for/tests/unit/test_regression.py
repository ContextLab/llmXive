"""
Unit tests for statistical regression analysis (T030, T031).

These tests validate the statistical outputs of the logistic regression
and McNemar's test implementations using synthetic data with known properties.
This ensures the statistical logic is sound before running on real data.

Dependencies:
- statsmodels
- numpy
- pandas
- scipy
"""
import json
import tempfile
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

# Import the analysis modules we are testing
# Note: These imports assume the modules exist as per the project structure
try:
    from src.analysis.regression import fit_regression, run_mcnemar
    from src.analysis.metrics import compute_metrics
except ImportError as e:
    # If the modules don't exist yet, we skip these specific imports in the mock setup
    # but the test structure remains valid for when they do.
    fit_regression = None
    run_mcnemar = None
    compute_metrics = None


class TestLogisticRegression(unittest.TestCase):
    """Tests for the logistic regression implementation (T030)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_path = Path(self.temp_dir.name) / "test_data.csv"
        
        # Create synthetic data with known properties
        # We'll create a dataset where:
        # - Feature X1 has a strong positive correlation with the target
        # - Feature X2 has no correlation with the target
        # - Language and CWE category are categorical
        
        np.random.seed(42)
        n_samples = 200
        
        # Generate features
        x1 = np.random.normal(0, 1, n_samples)
        x2 = np.random.normal(0, 1, n_samples)
        language = np.random.choice(['python', 'c', 'javascript'], n_samples)
        cwe_category = np.random.choice(['CWE-89', 'CWE-79', 'CWE-120'], n_samples)
        
        # Create target with known relationship: P(y=1) = sigmoid(2*x1 - 1)
        # This ensures x1 has a positive coefficient
        logit = 2 * x1 - 1
        probs = 1 / (1 + np.exp(-logit))
        target = np.random.binomial(1, probs, n_samples)
        
        # Create DataFrame
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'language': language,
            'cwe_category': cwe_category,
            'target': target
        })
        
        df.to_csv(self.test_data_path, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    @unittest.skipIf(fit_regression is None, "Regression module not available")
    def test_regression_coefficients_direction(self):
        """Test that the regression correctly identifies the direction of coefficients."""
        # Run regression
        result = fit_regression(
            input_path=str(self.test_data_path),
            target_col='target',
            output_path=os.path.join(self.temp_dir.name, "regression_test.json")
        )
        
        # Verify the result structure
        self.assertIn('coefficients', result)
        self.assertIn('p_values', result)
        self.assertIn('pseudo_r2', result)
        self.assertIn('adjusted_r2', result)
        
        # The coefficient for x1 should be positive (we set it to 2)
        # Note: Due to sampling noise, it might not be exactly 2, but should be > 0
        x1_coef = result['coefficients'].get('x1', 0)
        self.assertGreater(x1_coef, 0, 
            f"Expected positive coefficient for x1, got {x1_coef}. "
            "This suggests the regression is not correctly capturing the relationship.")
        
        # The p-value for x1 should be significant (< 0.05)
        x1_pval = result['p_values'].get('x1', 1.0)
        self.assertLess(x1_pval, 0.05, 
            f"Expected significant p-value for x1, got {x1_pval}. "
            "This suggests the regression is not correctly identifying the relationship.")

    @unittest.skipIf(fit_regression is None, "Regression module not available")
    def test_regression_null_feature(self):
        """Test that the regression correctly identifies null features."""
        result = fit_regression(
            input_path=str(self.test_data_path),
            target_col='target',
            output_path=os.path.join(self.temp_dir.name, "regression_test.json")
        )
        
        # x2 was generated with no relationship to the target
        # Its coefficient should be close to 0 and p-value should be high
        x2_coef = result['coefficients'].get('x2', 0)
        x2_pval = result['p_values'].get('x2', 1.0)
        
        # Allow some tolerance due to sampling noise
        self.assertLess(abs(x2_coef), 0.5, 
            f"Expected x2 coefficient to be near 0, got {x2_coef}")
        self.assertGreater(x2_pval, 0.1, 
            f"Expected x2 to be non-significant, got p-value {x2_pval}")


class TestMcNemarTest(unittest.TestCase):
    """Tests for McNemar's test implementation (T031)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create synthetic prediction data for McNemar's test
        # We'll create a contingency table where:
        # - LLM and Static Analyzer agree on most cases
        # - There are specific disagreements that we can test
        
        # Contingency table format:
        #                Static Analyzer
        #                Positive   Negative
        # LLM Positive      a          b
        # LLM Negative      c          d
        
        # We'll create a scenario where LLM has more false positives
        # and Static Analyzer has more false negatives
        self.contingency_table = {
            'llm_positive_static_positive': 80,  # a
            'llm_positive_static_negative': 15,  # b (LLM FP)
            'llm_negative_static_positive': 5,   # c (Static FP)
            'llm_negative_static_negative': 100  # d
        }

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    @unittest.skipIf(run_mcnemar is None, "McNemar module not available")
    def test_mcnemar_asymmetry_detection(self):
        """Test that McNemar's test correctly detects asymmetry in disagreements."""
        # Run McNemar's test
        result = run_mcnemar(
            contingency_table=self.contingency_table,
            output_path=os.path.join(self.temp_dir.name, "mcnemar_test.json")
        )
        
        # Verify the result structure
        self.assertIn('chi2_statistic', result)
        self.assertIn('p_value', result)
        self.assertIn('conclusion', result)
        
        # In our test case, b (15) != c (5), so we expect a significant result
        # The test should detect this asymmetry
        p_value = result['p_value']
        self.assertLess(p_value, 0.05, 
            f"Expected significant p-value due to asymmetry in disagreements, got {p_value}")

    @unittest.skipIf(run_mcnemar is None, "McNemar module not available")
    def test_mcnemar_symmetry(self):
        """Test that McNemar's test correctly handles symmetric disagreements."""
        # Create a symmetric contingency table
        symmetric_table = {
            'llm_positive_static_positive': 80,
            'llm_positive_static_negative': 10,  # b
            'llm_negative_static_positive': 10,  # c (equal to b)
            'llm_negative_static_negative': 100
        }
        
        result = run_mcnemar(
            contingency_table=symmetric_table,
            output_path=os.path.join(self.temp_dir.name, "mcnemar_symmetric.json")
        )
        
        # When b == c, the chi2 statistic should be 0 and p-value should be 1.0
        p_value = result['p_value']
        self.assertGreater(p_value, 0.5, 
            f"Expected non-significant p-value for symmetric disagreements, got {p_value}")


class TestRegressionIntegration(unittest.TestCase):
    """Integration tests for the full regression pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a more comprehensive test dataset
        np.random.seed(123)
        n_samples = 500
        
        # Generate features
        ast_depth = np.random.randint(2, 10, n_samples)
        cyclomatic_complexity = np.random.randint(1, 20, n_samples)
        embedding_similarity = np.random.uniform(0, 1, n_samples)
        language = np.random.choice(['python', 'c', 'javascript'], n_samples)
        cwe_category = np.random.choice(['CWE-89', 'CWE-79', 'CWE-120'], n_samples)
        
        # Create target with a complex relationship
        logit = (
            0.5 * ast_depth +
            0.3 * cyclomatic_complexity -
            0.2 * embedding_similarity +
            (1 if language == 'python' else 0) +
            (0.5 if cwe_category == 'CWE-89' else 0)
        )
        probs = 1 / (1 + np.exp(-logit))
        target = np.random.binomial(1, probs, n_samples)
        
        df = pd.DataFrame({
            'ast_depth': ast_depth,
            'cyclomatic_complexity': cyclomatic_complexity,
            'embedding_similarity': embedding_similarity,
            'language': language,
            'cwe_category': cwe_category,
            'target': target
        })
        
        self.test_data_path = Path(self.temp_dir.name) / "integration_test.csv"
        df.to_csv(self.test_data_path, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    @unittest.skipIf(fit_regression is None, "Regression module not available")
    def test_full_regression_pipeline(self):
        """Test the full regression pipeline with realistic data."""
        # Run regression
        result = fit_regression(
            input_path=str(self.test_data_path),
            target_col='target',
            output_path=os.path.join(self.temp_dir.name, "integration_regression.json")
        )
        
        # Verify all expected keys are present
        expected_keys = ['coefficients', 'p_values', 'pseudo_r2', 'adjusted_r2']
        for key in expected_keys:
            self.assertIn(key, result, f"Missing key '{key}' in regression result")
        
        # Verify that coefficients exist for all features
        expected_features = ['ast_depth', 'cyclomatic_complexity', 'embedding_similarity']
        for feature in expected_features:
            self.assertIn(feature, result['coefficients'], 
                f"Missing coefficient for feature '{feature}'")
            self.assertIn(feature, result['p_values'], 
                f"Missing p-value for feature '{feature}'")
        
        # Verify that R-squared values are in valid range
        self.assertGreaterEqual(result['pseudo_r2'], 0, 
            f"Pseudo R-squared should be non-negative, got {result['pseudo_r2']}")
        self.assertLessEqual(result['pseudo_r2'], 1, 
            f"Pseudo R-squared should be <= 1, got {result['pseudo_r2']}")
        
        self.assertGreaterEqual(result['adjusted_r2'], 0, 
            f"Adjusted R-squared should be non-negative, got {result['adjusted_r2']}")
        self.assertLessEqual(result['adjusted_r2'], 1, 
            f"Adjusted R-squared should be <= 1, got {result['adjusted_r2']}")


if __name__ == '__main__':
    unittest.main()