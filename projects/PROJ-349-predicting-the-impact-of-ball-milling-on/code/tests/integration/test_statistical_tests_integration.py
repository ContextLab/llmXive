"""
Integration test for T047: Statistical Test Implementation.

Verifies that the Nadeau & Bengio t-test works correctly in a realistic
scenario with synthetic but structurally valid data.
"""
import pytest
import numpy as np
from src.evaluate.statistical_tests import compare_models


class TestStatisticalTestsIntegration:
    """Integration tests for statistical comparison."""
    
    def test_realistic_model_comparison(self):
        """
        Simulate a realistic scenario where two models are compared
        across 10 outer folds of nested cross-validation.
        """
        # Simulate R² scores for 10 folds
        # Model A (GPR) is slightly better on average
        np.random.seed(42)
        n_folds = 10
        
        # True mean difference is 0.05, with some noise
        base_score = 0.75
        noise = np.random.normal(0, 0.02, n_folds)
        
        model_a_scores = base_score + 0.05 + noise
        model_b_scores = base_score + noise
        
        # Ensure no negative scores (clamp)
        model_a_scores = np.clip(model_a_scores, 0.0, 1.0)
        model_b_scores = np.clip(model_b_scores, 0.0, 1.0)
        
        # Simulate dataset: 1000 samples, 80/20 split
        n_train = 800
        n_test = 200
        
        result = compare_models(
            model_a_scores.tolist(),
            model_b_scores.tolist(),
            n_train,
            n_test
        )
        
        # Verify structure
        assert result["is_significant"] is True, \
            "Expected significant difference given the synthetic setup"
        assert result["mean_diff"] > 0, "Model A should have higher mean"
        assert result["p_value"] < 0.05
        
        # Verify the correction was applied (t-statistic should be reasonable)
        # Without correction, t would be higher. With correction, it's lower.
        # We just verify it's not infinite or NaN
        assert np.isfinite(result["t_statistic"])
        
    def test_consistency_with_manual_calculation(self):
        """
        Verify that the implementation matches a manual calculation
        on a small, fixed dataset.
        """
        # Fixed dataset
        model_a = [0.85, 0.88, 0.82, 0.90, 0.87]
        model_b = [0.80, 0.85, 0.81, 0.88, 0.84]
        n_train = 800
        n_test = 200
        
        result = compare_models(model_a, model_b, n_train, n_test)
        
        # Manual calculation
        diff = np.array(model_a) - np.array(model_b)
        mean_diff = np.mean(diff)
        var_diff = np.var(diff, ddof=1)
        k = len(diff)
        correction = (1.0 / k) + (n_test / n_train)
        se = np.sqrt(correction * var_diff)
        expected_t = mean_diff / se
        
        # Check t-statistic
        assert np.isclose(result["t_statistic"], expected_t, rtol=1e-5), \
            f"T-statistic mismatch: {result['t_statistic']} vs {expected_t}"
        
        # Check mean difference
        assert np.isclose(result["mean_diff"], mean_diff, rtol=1e-10)
