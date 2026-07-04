"""
Unit tests for ordinal regression model fitting with synthetic metadata.

This test suite validates the ordinal regression implementation in code/analyze.py
using synthetic metadata that mimics the structure of real experimental data.
"""
import pytest
import numpy as np
import pandas as pd
from statsmodels.miscmodels.ordinal_model import OrderedModel
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analyze import fit_ordinal_regression, get_model_summary

class TestOrdinalRegression:
    """Test cases for ordinal regression model fitting."""

    def _create_synthetic_metadata(self, n_samples=100):
        """
        Create synthetic metadata mimicking real experimental data.
        
        Args:
            n_samples: Number of synthetic samples to generate
            
        Returns:
            tuple: (X_features, y_trust) where:
                - X_features: DataFrame with consistency_score, avatar_type, 
                              duration, difficulty
                - y_trust: Series of ordinal trust scores (1-5)
        """
        np.random.seed(42)  # For reproducibility

        # Generate synthetic features
        consistency_score = np.random.uniform(0, 1, n_samples)
        avatar_type = np.random.choice(['emotional', 'neutral', 'expressive'], n_samples)
        duration = np.random.uniform(30, 300, n_samples)  # 30s to 300s
        difficulty = np.random.choice([1, 2, 3, 4, 5], n_samples)

        # Generate ordinal trust scores (1-5) with some correlation to consistency
        # Higher consistency should generally lead to higher trust
        base_trust = 3 + 2 * consistency_score  # Base score influenced by consistency
        noise = np.random.normal(0, 0.8, n_samples)  # Add noise
        raw_trust = base_trust + noise + (difficulty * 0.1)  # Slight difficulty effect

        # Clip and convert to ordinal categories 1-5
        trust_scores = np.clip(raw_trust, 1, 5).astype(int)

        # Create DataFrame
        X = pd.DataFrame({
            'consistency_score': consistency_score,
            'avatar_type': avatar_type,
            'duration': duration,
            'difficulty': difficulty
        })

        y = pd.Series(trust_scores, name='trust_score')

        return X, y

    def test_fit_ordinal_regression_basic(self):
        """Test basic fitting of ordinal regression model."""
        X, y = self._create_synthetic_metadata(n_samples=200)
        
        # Fit the model
        model, results = fit_ordinal_regression(X, y)
        
        # Verify model is not None
        assert model is not None, "Model should not be None"
        assert results is not None, "Results should not be None"
        
        # Verify results have expected attributes
        assert hasattr(results, 'params'), "Results should have 'params' attribute"
        assert hasattr(results, 'pvalues'), "Results should have 'pvalues' attribute"
        assert hasattr(results, 'rsquared_pseudo'), "Results should have 'rsquared_pseudo' attribute"
        
        # Check that consistency_score parameter exists
        assert 'consistency_score' in results.params.index, \
            "consistency_score should be in model parameters"

    def test_fit_ordinal_regression_with_controls(self):
        """Test fitting with control variables (avatar_type, duration, difficulty)."""
        X, y = self._create_synthetic_metadata(n_samples=300)
        
        model, results = fit_ordinal_regression(X, y)
        
        # Check that all control variables are in the model
        param_index = results.params.index
        assert 'avatar_type' in param_index or any('avatar_type' in str(idx) for idx in param_index), \
            "avatar_type should be included as a control variable"
        assert 'duration' in param_index, "duration should be in model parameters"
        assert 'difficulty' in param_index, "difficulty should be in model parameters"

    def test_fit_ordinal_regression_small_sample(self):
        """Test fitting with a very small sample to ensure robustness."""
        X, y = self._create_synthetic_metadata(n_samples=30)
        
        # This should not raise an exception, though results may not be statistically significant
        model, results = fit_ordinal_regression(X, y)
        
        assert model is not None
        assert results is not None

    def test_get_model_summary_structure(self):
        """Test that get_model_summary returns expected structure."""
        X, y = self._create_synthetic_metadata(n_samples=150)
        
        model, results = fit_ordinal_regression(X, y)
        summary = get_model_summary(results)
        
        # Verify summary is a dictionary
        assert isinstance(summary, dict), "Summary should be a dictionary"
        
        # Verify expected keys
        expected_keys = ['consistency_score_coef', 'consistency_score_pvalue', 
                       'pseudo_r_squared', 'control_variables']
        for key in expected_keys:
            assert key in summary, f"Summary should contain '{key}'"
        
        # Verify types
        assert isinstance(summary['consistency_score_coef'], (int, float)), \
            "consistency_score_coef should be numeric"
        assert isinstance(summary['consistency_score_pvalue'], (int, float)), \
            "consistency_score_pvalue should be numeric"
        assert isinstance(summary['pseudo_r_squared'], (int, float)), \
            "pseudo_r_squared should be numeric"
        assert isinstance(summary['control_variables'], dict), \
            "control_variables should be a dictionary"

    def test_get_model_summary_values(self):
        """Test that model summary values are within expected ranges."""
        X, y = self._create_synthetic_metadata(n_samples=200)
        
        model, results = fit_ordinal_regression(X, y)
        summary = get_model_summary(results)
        
        # Pseudo R-squared should be between 0 and 1 (or close to it)
        assert 0 <= summary['pseudo_r_squared'] <= 1.5, \
            f"Pseudo R-squared should be between 0 and 1.5, got {summary['pseudo_r_squared']}"
        
        # P-values should be between 0 and 1
        assert 0 <= summary['consistency_score_pvalue'] <= 1, \
            f"P-value should be between 0 and 1, got {summary['consistency_score_pvalue']}"

    def test_fit_ordinal_regression_significant_consistency(self):
        """
        Test that when consistency has a strong effect, 
        the model detects it as significant.
        """
        # Create data with strong consistency effect
        np.random.seed(123)
        n_samples = 500
        consistency = np.random.uniform(0, 1, n_samples)
        
        # Strong positive effect of consistency on trust
        base_trust = 2 + 3 * consistency  
        noise = np.random.normal(0, 0.5, n_samples)
        raw_trust = base_trust + noise
        trust_scores = np.clip(raw_trust, 1, 5).astype(int)
        
        X = pd.DataFrame({'consistency_score': consistency, 
                        'avatar_type': ['neutral'] * n_samples,
                        'duration': [60] * n_samples,
                        'difficulty': [3] * n_samples})
        y = pd.Series(trust_scores)
        
        model, results = fit_ordinal_regression(X, y)
        summary = get_model_summary(results)
        
        # With strong effect and large sample, p-value should be low
        # Note: This is probabilistic, so we allow some tolerance
        assert summary['consistency_score_pvalue'] < 0.1, \
            f"Expected significant consistency effect (p < 0.1), got p={summary['consistency_score_pvalue']}"
        
        # Coefficient should be positive
        assert summary['consistency_score_coef'] > 0, \
            "Consistency coefficient should be positive"

    def test_fit_ordinal_regression_error_handling(self):
        """Test error handling with invalid input."""
        # Test with empty DataFrame
        X_empty = pd.DataFrame()
        y_empty = pd.Series()
        
        with pytest.raises(Exception):
            fit_ordinal_regression(X_empty, y_empty)

        # Test with mismatched lengths
        X_mismatch = pd.DataFrame({'consistency_score': [0.5, 0.6]})
        y_mismatch = pd.Series([1, 2, 3])
        
        with pytest.raises(Exception):
            fit_ordinal_regression(X_mismatch, y_mismatch)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
