"""
Unit tests for metrics computation (src/evaluation/metrics.py).
Tests F1 score and MAPE calculations including edge cases.
"""
import pytest
import numpy as np
from src.evaluation.metrics import compute_f1, compute_mape


class TestComputeF1:
    """Test suite for F1 score computation."""

    def test_perfect_prediction(self):
        """Test F1 score with perfect predictions."""
        y_true = [1, 1, 1, 0, 0, 0]
        y_pred = [1, 1, 1, 0, 0, 0]
        
        f1 = compute_f1(y_true, y_pred)
        
        assert f1 == 1.0

    def test_no_true_positives(self):
        """Test F1 score when there are no true positives."""
        y_true = [1, 1, 1, 0, 0, 0]
        y_pred = [0, 0, 0, 0, 0, 0]
        
        f1 = compute_f1(y_true, y_pred)
        
        assert f1 == 0.0

    def test_multiclass_f1(self):
        """Test F1 score for multiclass classification."""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 1, 2]
        
        f1 = compute_f1(y_true, y_pred)
        
        assert f1 == 1.0

    def test_imbalanced_classes(self):
        """Test F1 score with imbalanced class distribution."""
        y_true = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        y_pred = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        f1 = compute_f1(y_true, y_pred)
        
        assert f1 == 1.0

    def test_partial_correctness(self):
        """Test F1 score with partial correctness."""
        y_true = [1, 1, 1, 0, 0, 0]
        y_pred = [1, 0, 1, 0, 1, 0]
        
        f1 = compute_f1(y_true, y_pred)
        
        # Precision = 2/3, Recall = 2/3, F1 = 2/3
        expected_f1 = 2.0 / 3.0
        assert abs(f1 - expected_f1) < 1e-6

    def test_empty_arrays(self):
        """Test F1 score with empty arrays."""
        y_true = []
        y_pred = []
        
        f1 = compute_f1(y_true, y_pred)
        
        assert f1 == 0.0

    def test_numpy_arrays(self):
        """Test F1 score with numpy arrays."""
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([1, 0, 0, 0])
        
        f1 = compute_f1(y_true, y_pred)
        
        assert isinstance(f1, float)
        assert f1 > 0.0

    def test_float_labels(self):
        """Test F1 score with float labels."""
        y_true = [1.0, 1.0, 0.0, 0.0]
        y_pred = [1.0, 0.0, 0.0, 0.0]
        
        f1 = compute_f1(y_true, y_pred)
        
        assert isinstance(f1, float)

    def test_invalid_input_types(self):
        """Test F1 score with invalid input types."""
        with pytest.raises(TypeError):
            compute_f1("not", "lists")


class TestComputeMape:
    """Test suite for Mean Absolute Percentage Error computation."""

    def test_perfect_prediction(self):
        """Test MAPE with perfect predictions."""
        y_true = [100, 200, 300]
        y_pred = [100, 200, 300]
        
        mape = compute_mape(y_true, y_pred)
        
        assert mape == 0.0

    def test_consistent_error(self):
        """Test MAPE with consistent error percentage."""
        y_true = [100, 200, 300]
        y_pred = [110, 220, 330]  # 10% error each
        
        mape = compute_mape(y_true, y_pred)
        
        assert abs(mape - 10.0) < 1e-6

    def test_negative_values(self):
        """Test MAPE with negative values."""
        y_true = [-100, -200, -300]
        y_pred = [-110, -220, -330]
        
        mape = compute_mape(y_true, y_pred)
        
        assert abs(mape - 10.0) < 1e-6

    def test_mixed_signs(self):
        """Test MAPE with mixed positive and negative values."""
        y_true = [100, -100, 200]
        y_pred = [110, -110, 220]
        
        mape = compute_mape(y_true, y_pred)
        
        assert mape > 0.0

    def test_zero_true_value(self):
        """Test MAPE handling of zero true values (division by zero)."""
        y_true = [0, 100, 200]
        y_pred = [0, 110, 220]
        
        # Should handle zero gracefully
        mape = compute_mape(y_true, y_pred)
        
        # Either returns 0 or ignores the zero entry
        assert mape >= 0.0

    def test_all_zeros(self):
        """Test MAPE with all zero true values."""
        y_true = [0, 0, 0]
        y_pred = [1, 2, 3]
        
        mape = compute_mape(y_true, y_pred)
        
        # Should not crash, likely returns 0.0
        assert mape == 0.0

    def test_empty_arrays(self):
        """Test MAPE with empty arrays."""
        y_true = []
        y_pred = []
        
        mape = compute_mape(y_true, y_pred)
        
        assert mape == 0.0

    def test_numpy_arrays(self):
        """Test MAPE with numpy arrays."""
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([110.0, 220.0, 330.0])
        
        mape = compute_mape(y_true, y_pred)
        
        assert isinstance(mape, float)
        assert abs(mape - 10.0) < 1e-6

    def test_large_values(self):
        """Test MAPE with very large values."""
        y_true = [1e10, 2e10, 3e10]
        y_pred = [1.1e10, 2.2e10, 3.3e10]
        
        mape = compute_mape(y_true, y_pred)
        
        assert abs(mape - 10.0) < 1e-6

    def test_small_values(self):
        """Test MAPE with very small values."""
        y_true = [1e-10, 2e-10, 3e-10]
        y_pred = [1.1e-10, 2.2e-10, 3.3e-10]
        
        mape = compute_mape(y_true, y_pred)
        
        assert abs(mape - 10.0) < 1e-6

    def test_invalid_input_types(self):
        """Test MAPE with invalid input types."""
        with pytest.raises(TypeError):
            compute_mape("not", "lists")

    def test_single_element(self):
        """Test MAPE with single element arrays."""
        y_true = [100]
        y_pred = [110]
        
        mape = compute_mape(y_true, y_pred)
        
        assert abs(mape - 10.0) < 1e-6