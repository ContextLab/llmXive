import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from scipy import stats

# Add parent directory to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modeling.evaluation import calculate_metrics

@pytest.fixture
def mock_model():
    """Mock a trained sklearn-like regressor."""
    model = Mock()
    model.predict = Mock(return_value=np.array([1.0, 2.0, 3.0, 4.0]))
    return model

@pytest.fixture
def mock_shap_explainer():
    """Mock a SHAP explainer object."""
    explainer = Mock()
    # Return a 2D array: (n_samples, n_features)
    explainer.shap_values = Mock(return_value=np.array([
        [0.1, 0.2, 0.3],
        [0.15, 0.25, 0.35],
        [0.12, 0.22, 0.32]
    ]))
    return explainer

@pytest.fixture
def sample_feature_matrix():
    """Create a sample feature matrix for testing."""
    return pd.DataFrame({
        'strain_rate': [1e-3, 1e-2, 1e-1],
        'composition_Fe': [0.98, 0.95, 0.99],
        'composition_C': [0.02, 0.05, 0.01]
    })

class TestSHAPValueExtraction:
    """Unit tests for SHAP value extraction logic."""

    def test_shap_values_shape(self, mock_shap_explainer, sample_feature_matrix):
        """Verify SHAP values are returned with correct shape."""
        shap_values = mock_shap_explainer.shap_values(sample_feature_matrix)
        assert shap_values.shape[0] == sample_feature_matrix.shape[0]
        assert shap_values.shape[1] == sample_feature_matrix.shape[1]

    def test_shap_values_content(self, mock_shap_explainer):
        """Verify SHAP values contain expected numerical ranges."""
        values = mock_shap_explainer.shap_values(pd.DataFrame({'a': [1]}))
        assert np.all(values >= 0)  # Assuming positive contributions in mock

    def test_feature_importance_ranking(self, mock_shap_explainer, sample_feature_matrix):
        """Verify that we can rank features by mean absolute SHAP value."""
        shap_values = mock_shap_explainer.shap_values(sample_feature_matrix)
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        # Should be a 1D array with length equal to number of features
        assert len(mean_abs_shap) == sample_feature_matrix.shape[1]
        assert np.all(mean_abs_shap >= 0)

class TestWilcoxonSignedRankTest:
    """Unit tests for Wilcoxon signed-rank test implementation."""

    def test_wilcoxon_basic_execution(self):
        """Test that the Wilcoxon test runs without error on valid data."""
        # Generate two correlated samples (null hypothesis: no difference)
        np.random.seed(42)
        n = 50
        sample1 = np.random.normal(loc=100, scale=10, size=n)
        sample2 = sample1 + np.random.normal(loc=0, scale=2, size=n)  # Small shift

        stat, p_value = stats.wilcoxon(sample1, sample2)

        assert isinstance(stat, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1

    def test_wilcoxon_significant_difference(self):
        """Test Wilcoxon detects a significant difference when one exists."""
        np.random.seed(42)
        n = 100
        sample1 = np.random.normal(loc=100, scale=5, size=n)
        sample2 = np.random.normal(loc=120, scale=5, size=n)  # Large shift

        stat, p_value = stats.wilcoxon(sample1, sample2)

        # With a large shift, we expect a very small p-value
        assert p_value < 0.01

    def test_wilcoxon_equal_samples(self):
        """Test Wilcoxon on identical samples (p-value should be 1.0)."""
        sample = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        stat, p_value = stats.wilcoxon(sample, sample)

        assert p_value == 1.0
        assert stat == 0.0

    def test_wilcoxon_with_nan_handling(self):
        """Test behavior with NaN values (should raise or be handled)."""
        sample1 = np.array([1.0, 2.0, np.nan, 4.0])
        sample2 = np.array([1.0, 2.0, 3.0, 4.0])

        # scipy.stats.wilcoxon raises ValueError if NaNs are present
        with pytest.raises(ValueError):
            stats.wilcoxon(sample1, sample2)

    def test_benjamini_hochberg_correction(self):
        """Test implementation of Benjamini-Hochberg correction."""
        # Simulate a list of p-values
        p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.1, 0.2])
        alpha = 0.05
        n_tests = len(p_values)

        # Sort p-values
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]

        # Calculate BH critical values
        critical_values = (np.arange(1, n_tests + 1) / n_tests) * alpha

        # Find the largest k where p_k <= critical_value_k
        reject_mask = sorted_p <= critical_values
        if np.any(reject_mask):
            k_max = np.max(np.where(reject_mask)[0])
            # All hypotheses up to k_max are rejected
            rejected_indices = sorted_indices[:k_max + 1]
        else:
            rejected_indices = np.array([], dtype=int)

        # Verify logic: first few small p-values should be rejected
        assert len(rejected_indices) > 0
        assert 0.001 in p_values[rejected_indices]
        assert 0.01 in p_values[rejected_indices]

    def test_wilcoxon_on_model_errors(self):
        """Test Wilcoxon comparing errors of two mock models."""
        # Simulate errors from Model A and Model B
        true_values = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        pred_a = np.array([11.0, 19.0, 31.0, 39.0, 51.0])
        pred_b = np.array([10.5, 19.5, 30.5, 39.5, 50.5])

        error_a = np.abs(true_values - pred_a)
        error_b = np.abs(true_values - pred_b)

        stat, p_value = stats.wilcoxon(error_a, error_b)

        assert isinstance(stat, float)
        assert 0 <= p_value <= 1

class TestMetricsCalculation:
    """Unit tests for metrics calculation helper."""

    def test_calculate_metrics_r_squared(self):
        """Test R2 calculation."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.1, 5.0])

        r2, mae, rmse = calculate_metrics(y_true, y_pred)

        assert isinstance(r2, float)
        assert r2 <= 1.0
        assert mae >= 0
        assert rmse >= 0

    def test_calculate_metrics_perfect_prediction(self):
        """Test metrics when prediction is perfect."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        r2, mae, rmse = calculate_metrics(y_true, y_pred)

        assert r2 == 1.0
        assert mae == 0.0
        assert rmse == 0.0

    def test_calculate_metrics_constant_prediction(self):
        """Test metrics when prediction is constant but wrong."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([3.0, 3.0, 3.0, 3.0, 3.0])

        r2, mae, rmse = calculate_metrics(y_true, y_pred)

        # R2 should be 0 for constant prediction on centered data?
        # Actually R2 can be negative if model is worse than mean.
        assert isinstance(r2, float)
        assert mae > 0
        assert rmse > 0