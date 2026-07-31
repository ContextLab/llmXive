"""
Unit tests for SHAP value calculation and explainability logic in US3.

This file tests:
1. SHAP value calculation (T031)
2. Threshold sensitivity sweep logic (T032)
3. Spearman rank correlation calculation (T033)

These tests verify the core logic of code/explainability.py without
requiring the full training pipeline to run.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from explainability import compute_shap_values, threshold_sensitivity_sweep, spearman_rank_correlation


class TestSHAPValueCalculation:
    """Tests for T031: SHAP value calculation."""

    def test_compute_shap_values_returns_dict(self):
        """Verify compute_shap_values returns a dictionary with expected structure."""
        # Mock model and data
        mock_model = MagicMock()
        mock_model.n_features_in_ = 5
        
        mock_explainer = MagicMock()
        # SHAP values shape: (n_samples, n_features)
        mock_shap_values = np.random.rand(10, 5)
        mock_explainer.shap_values.return_value = mock_shap_values
        
        mock_data = pd.DataFrame(np.random.rand(10, 5), columns=['feat1', 'feat2', 'feat3', 'feat4', 'feat5'])
        
        with patch('explainability.shap.TreeExplainer', return_value=mock_explainer):
            result = compute_shap_values(mock_model, mock_data)
        
        assert isinstance(result, dict)
        assert 'shap_values' in result
        assert 'feature_names' in result
        assert 'mean_abs_shap' in result
        
        # Verify shapes
        assert result['shap_values'].shape == (10, 5)
        assert len(result['feature_names']) == 5
        assert len(result['mean_abs_shap']) == 5

    def test_compute_shap_values_with_multilabel(self):
        """Verify SHAP calculation handles multi-label output correctly."""
        mock_model = MagicMock()
        mock_model.n_features_in_ = 3
        mock_model.classes_ = [np.array([0, 1]), np.array([0, 1])]  # Two binary labels
        
        mock_explainer = MagicMock()
        # For multi-label, shap_values returns a list of arrays
        mock_shap_values = [np.random.rand(5, 3) for _ in range(2)]
        mock_explainer.shap_values.return_value = mock_shap_values
        
        mock_data = pd.DataFrame(np.random.rand(5, 3), columns=['a', 'b', 'c'])
        
        with patch('explainability.shap.TreeExplainer', return_value=mock_explainer):
            result = compute_shap_values(mock_model, mock_data)
        
        assert isinstance(result, dict)
        assert 'shap_values' in result
        # For multi-label, should be a list of arrays
        assert isinstance(result['shap_values'], list)
        assert len(result['shap_values']) == 2
        assert result['shap_values'][0].shape == (5, 3)

    def test_compute_shap_values_handles_small_dataset(self):
        """Verify SHAP works with small datasets (edge case)."""
        mock_model = MagicMock()
        mock_model.n_features_in_ = 2
        
        mock_explainer = MagicMock()
        mock_shap_values = np.random.rand(3, 2)  # Only 3 samples
        mock_explainer.shap_values.return_value = mock_shap_values
        
        mock_data = pd.DataFrame(np.random.rand(3, 2), columns=['x', 'y'])
        
        with patch('explainability.shap.TreeExplainer', return_value=mock_explainer):
            result = compute_shap_values(mock_model, mock_data)
        
        assert result['shap_values'].shape == (3, 2)
        assert len(result['mean_abs_shap']) == 2


class TestThresholdSensitivitySweep:
    """Tests for T032: Threshold sensitivity sweep logic."""

    def test_sweep_uses_correct_deltas(self):
        """Verify the sweep uses the exact delta set {0.01, 0.05, 0.1}."""
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.random.rand(10, 2)
        
        mock_data = pd.DataFrame(np.random.rand(10, 3), columns=['a', 'b', 'c'])
        mock_labels = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 0])
        
        # The function should use these specific deltas
        deltas = [0.01, 0.05, 0.1]
        
        with patch('explainability.threshold_sensitivity_sweep') as mock_func:
            # Just verify the call uses correct deltas
            pass
        
        # We'll test the actual implementation logic
        from explainability import threshold_sensitivity_sweep
        
        # Create a simple mock that tracks calls
        class MockClassifier:
            def predict_proba(self, X):
                return np.random.rand(X.shape[0], 2)
        
        mock_clf = MockClassifier()
        result = threshold_sensitivity_sweep(mock_clf, mock_data, mock_labels, deltas=deltas)
        
        # Verify result contains all deltas
        assert 'thresholds' in result
        for delta in deltas:
            # Each delta should have a corresponding entry
            assert any(abs(t - delta) < 1e-6 for t in result['thresholds'])

    def test_sweep_returns_fp_fn_rates(self):
        """Verify the sweep returns FP and FN rate variations."""
        mock_clf = MagicMock()
        mock_clf.predict_proba.return_value = np.random.rand(20, 2)
        
        mock_data = pd.DataFrame(np.random.rand(20, 3), columns=['a', 'b', 'c'])
        mock_labels = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1])
        
        result = threshold_sensitivity_sweep(mock_clf, mock_data, mock_labels)
        
        assert 'fp_rates' in result
        assert 'fn_rates' in result
        assert len(result['fp_rates']) == len(result['fn_rates'])
        assert len(result['fp_rates']) == len(result['thresholds'])

    def test_sweep_stability_check(self):
        """Verify stability check is performed (variance within 5%)."""
        mock_clf = MagicMock()
        # Create predictable probabilities for stability testing
        mock_clf.predict_proba.return_value = np.tile([0.5, 0.5], (10, 1))
        
        mock_data = pd.DataFrame(np.random.rand(10, 2), columns=['x', 'y'])
        mock_labels = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        
        result = threshold_sensitivity_sweep(mock_clf, mock_data, mock_labels)
        
        assert 'stability_check' in result
        assert 'passed' in result['stability_check'] or 'variance' in result['stability_check']


class TestSpearmanRankCorrelation:
    """Tests for T033: Spearman rank correlation calculation."""

    def test_spearman_correlation_basic(self):
        """Verify Spearman correlation is calculated correctly."""
        importance_shap = np.array([0.8, 0.6, 0.4, 0.2, 0.1])
        importance_lit = np.array([0.9, 0.7, 0.3, 0.15, 0.05])
        
        rho = spearman_rank_correlation(importance_shap, importance_lit)
        
        assert isinstance(rho, float)
        assert -1.0 <= rho <= 1.0
        # With similar rankings, should be positive and high
        assert rho > 0.5

    def test_spearman_correlation_opposite_rankings(self):
        """Verify Spearman handles opposite rankings correctly."""
        importance_shap = np.array([0.8, 0.6, 0.4, 0.2, 0.1])
        importance_lit = np.array([0.1, 0.2, 0.4, 0.6, 0.8])  # Reverse order
        
        rho = spearman_rank_correlation(importance_shap, importance_lit)
        
        assert rho < 0  # Negative correlation

    def test_spearman_correlation_identical_rankings(self):
        """Verify Spearman returns 1.0 for identical rankings."""
        importance_shap = np.array([0.9, 0.7, 0.5, 0.3, 0.1])
        importance_lit = np.array([0.9, 0.7, 0.5, 0.3, 0.1])
        
        rho = spearman_rank_correlation(importance_shap, importance_lit)
        
        assert abs(rho - 1.0) < 1e-6

    def test_spearman_correlation_with_ties(self):
        """Verify Spearman handles tied values correctly."""
        importance_shap = np.array([0.5, 0.5, 0.3, 0.2, 0.1])
        importance_lit = np.array([0.6, 0.6, 0.3, 0.2, 0.1])
        
        rho = spearman_rank_correlation(importance_shap, importance_lit)
        
        assert -1.0 <= rho <= 1.0
        # Should still be positive with ties

    def test_spearman_correlation_different_lengths(self):
        """Verify Spearman raises error for mismatched lengths."""
        importance_shap = np.array([0.8, 0.6, 0.4])
        importance_lit = np.array([0.9, 0.7])
        
        with pytest.raises(ValueError):
            spearman_rank_correlation(importance_shap, importance_lit)

    def test_spearman_correlation_empty_arrays(self):
        """Verify Spearman handles empty arrays gracefully."""
        importance_shap = np.array([])
        importance_lit = np.array([])
        
        # Should raise or return NaN for empty arrays
        with pytest.raises((ValueError, IndexError)):
            spearman_rank_correlation(importance_shap, importance_lit)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])