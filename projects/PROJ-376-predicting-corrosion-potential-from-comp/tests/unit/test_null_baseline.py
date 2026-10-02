import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.evaluate_null_baseline import (
    calculate_null_baseline_metrics,
    permutation_test_on_aggregated_predictions,
    classify_learnability,
    run_null_baseline_analysis
)

class TestNullBaseline:
    """Unit tests for null baseline evaluation functions."""

    def test_calculate_null_baseline_metrics(self):
        """Test that null baseline metrics are calculated correctly."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        
        metrics = calculate_null_baseline_metrics(y_true, y_pred)
        
        # Check that mean prediction is correct
        assert abs(metrics['mean_prediction'] - 3.0) < 1e-6
        
        # Check that R² for null model is 0.0 (since it's just the mean)
        assert abs(metrics['r2_null']) < 1e-6
        
        # Check that RMSE is positive
        assert metrics['rmse_null'] > 0

    def test_permutation_test_with_perfect_model(self):
        """Test permutation test with a perfect model (R² = 1.0)."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = y_true.copy()  # Perfect predictions
        
        observed_r2, p_value = permutation_test_on_aggregated_predictions(
            y_true, y_pred, n_permutations=100, random_state=42
        )
        
        # Observed R² should be 1.0
        assert abs(observed_r2 - 1.0) < 1e-6
        
        # P-value should be very small (close to 0)
        assert p_value < 0.1  # With 100 permutations, we expect a small p-value

    def test_permutation_test_with_random_predictions(self):
        """Test permutation test with random predictions (R² ~ 0)."""
        np.random.seed(42)
        y_true = np.random.randn(100)
        y_pred = np.random.randn(100)
        
        observed_r2, p_value = permutation_test_on_aggregated_predictions(
            y_true, y_pred, n_permutations=100, random_state=42
        )
        
        # Observed R² should be close to 0
        assert abs(observed_r2) < 0.5  # Not necessarily 0, but not extreme
        
        # P-value should be around 0.5 (random chance)
        # Note: With only 100 permutations, this is just a rough check
        assert 0.1 < p_value < 0.9

    def test_classify_learnability_learnable(self):
        """Test classification when model is learnable."""
        result = classify_learnability(observed_r2=0.5, p_value=0.01)
        
        assert result['is_learnable'] is True
        assert result['classification'] == 'learnable'

    def test_classify_learnability_not_learnable_r2(self):
        """Test classification when R² is too low."""
        result = classify_learnability(observed_r2=0.0, p_value=0.01)
        
        assert result['is_learnable'] is False
        assert result['classification'] == 'not_learnable'

    def test_classify_learnability_not_learnable_p(self):
        """Test classification when p-value is too high."""
        result = classify_learnability(observed_r2=0.5, p_value=0.1)
        
        assert result['is_learnable'] is False
        assert result['classification'] == 'not_learnable'

    def test_run_null_baseline_analysis(self):
        """Test the full null baseline analysis pipeline."""
        np.random.seed(42)
        y_true = np.random.randn(50)
        y_pred = y_true * 0.8 + np.random.randn(50) * 0.2
        
        results = run_null_baseline_analysis(y_true, y_pred, n_permutations=50, random_state=42)
        
        # Check structure
        assert 'null_baseline_metrics' in results
        assert 'permutation_test' in results
        assert 'learnability' in results
        
        # Check null baseline metrics
        assert 'r2_null' in results['null_baseline_metrics']
        assert 'rmse_null' in results['null_baseline_metrics']
        assert 'mean_prediction' in results['null_baseline_metrics']
        
        # Check permutation test
        assert 'observed_r2' in results['permutation_test']
        assert 'p_value' in results['permutation_test']
        assert 'n_permutations' in results['permutation_test']
        
        # Check learnability
        assert 'is_learnable' in results['learnability']
        assert 'classification' in results['learnability']

    def test_permutation_test_determinism(self):
        """Test that permutation test is deterministic with fixed seed."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        
        r2_1, p_1 = permutation_test_on_aggregated_predictions(
            y_true, y_pred, n_permutations=100, random_state=42
        )
        
        r2_2, p_2 = permutation_test_on_aggregated_predictions(
            y_true, y_pred, n_permutations=100, random_state=42
        )
        
        assert r2_1 == r2_2
        assert p_1 == p_2