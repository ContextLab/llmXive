"""
Unit tests for the modeling module (US3).

This file contains contract tests for:
- Ordinal Logistic Regression (T028)
- Random Forest Regression (T029)
- Binary Classification Fallback (T030)

These tests verify that the modeling components adhere to the specified
contracts (inputs, outputs, error handling) without requiring full
dataset processing or long training times.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.modeling import (
    train_ordinal_logistic_regression,
    train_random_forest_regression,
    train_binary_classification_fallback,
    calculate_vif,
    detect_degenerate_target,
    run_cross_validation,
    ModelResult
)
from code.utils.logger import setup_logger

logger = setup_logger("test_modeling")


class TestOrdinalLogisticRegression:
    """Contract tests for T028: Ordinal Logistic Regression."""

    @pytest.fixture
    def sample_data(self):
        """Generate a small synthetic dataset for contract testing."""
        np.random.seed(42)
        n_samples = 50
        
        # Create features (topological descriptors)
        X = np.random.rand(n_samples, 3)
        X = pd.DataFrame(X, columns=['wiener', 'balaban', 'zagreb'])
        
        # Create ordinal target (0, 1, 2) representing selectivity classes
        y = np.random.choice([0, 1, 2], size=n_samples)
        
        return X, y

    def test_returns_model_result_object(self, sample_data):
        """Verify train_ordinal_logistic_regression returns a ModelResult."""
        X, y = sample_data
        result = train_ordinal_logistic_regression(X, y)
        
        assert isinstance(result, ModelResult), "Must return ModelResult instance"
        assert result.model_type == "OrdinalLogisticRegression"
        assert result.is_success is True
        assert result.metrics is not None
        assert 'log_likelihood' in result.metrics

    def test_handles_empty_dataframe(self):
        """Verify behavior with empty input."""
        X = pd.DataFrame(columns=['wiener', 'balaban', 'zagreb'])
        y = np.array([])
        
        with pytest.raises((ValueError, IndexError)):
            train_ordinal_logistic_regression(X, y)

    def test_preserves_feature_names(self, sample_data):
        """Verify feature names are preserved in the result."""
        X, y = sample_data
        result = train_ordinal_logistic_regression(X, y)
        
        assert result.feature_names == list(X.columns)


class TestRandomForestRegression:
    """Contract tests for T029: Random Forest Regression."""

    @pytest.fixture
    def regression_data(self):
        """Generate a small synthetic dataset for regression contract testing."""
        np.random.seed(42)
        n_samples = 100
        
        # Create features (topological descriptors)
        X = np.random.rand(n_samples, 3)
        X = pd.DataFrame(X, columns=['wiener', 'balaban', 'zagreb'])
        
        # Create continuous target (simulating a regression task)
        # In the real pipeline, this would be the symmetry-derived target
        y = 0.5 * X['wiener'] + 0.3 * X['balaban'] + np.random.normal(0, 0.1, n_samples)
        
        return X, y

    def test_returns_model_result_object(self, regression_data):
        """Verify train_random_forest_regression returns a ModelResult."""
        X, y = regression_data
        result = train_random_forest_regression(X, y)
        
        assert isinstance(result, ModelResult), "Must return ModelResult instance"
        assert result.model_type == "RandomForestRegressor"
        assert result.is_success is True
        assert result.metrics is not None
        assert 'r_squared' in result.metrics
        assert 'mean_squared_error' in result.metrics

    def test_handles_small_dataset(self):
        """Verify behavior with very small dataset (edge case for CV)."""
        X = pd.DataFrame({'wiener': [10, 15], 'balaban': [2, 3], 'zagreb': [5, 6]})
        y = np.array([1.0, 2.0])
        
        # Should succeed, but might use LOO or a single fold depending on config
        result = train_random_forest_regression(X, y)
        
        assert isinstance(result, ModelResult)
        assert result.is_success is True

    def test_feature_importance_available(self, regression_data):
        """Verify feature importance is calculated and available."""
        X, y = regression_data
        result = train_random_forest_regression(X, y)
        
        assert hasattr(result, 'feature_importances')
        assert result.feature_importances is not None
        assert len(result.feature_importances) == len(X.columns)

    def test_handles_non_numeric_features(self):
        """Verify error handling for non-numeric features."""
        X = pd.DataFrame({
            'wiener': [10, 20, 30],
            'balaban': ['a', 'b', 'c'],  # Invalid
            'zagreb': [5, 6, 7]
        })
        y = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises((ValueError, TypeError)):
            train_random_forest_regression(X, y)

    def test_random_state_determinism(self, regression_data):
        """Verify that setting random_state produces deterministic results."""
        X, y = regression_data
        
        result1 = train_random_forest_regression(X, y, random_state=123)
        result2 = train_random_forest_regression(X, y, random_state=123)
        
        # Metrics should be identical
        assert result1.metrics['r_squared'] == result2.metrics['r_squared']
        assert np.allclose(result1.feature_importances, result2.feature_importances)


class TestBinaryClassificationFallback:
    """Contract tests for T030: Binary Classification Fallback."""

    @pytest.fixture
    def degenerate_data(self):
        """Data with a target that has low variance (degenerate)."""
        np.random.seed(42)
        n_samples = 50
        
        X = pd.DataFrame({
            'wiener': np.random.rand(n_samples) * 10,
            'balaban': np.random.rand(n_samples) * 5,
            'zagreb': np.random.rand(n_samples) * 20
        })
        
        # Create a binary target (0 or 1)
        y = np.random.choice([0, 1], size=n_samples)
        
        return X, y

    def test_returns_model_result_object(self, degenerate_data):
        """Verify train_binary_classification_fallback returns a ModelResult."""
        X, y = degenerate_data
        result = train_binary_classification_fallback(X, y)
        
        assert isinstance(result, ModelResult), "Must return ModelResult instance"
        assert result.model_type == "BinaryClassifier"
        assert result.is_success is True
        assert result.metrics is not None
        assert 'accuracy' in result.metrics
        assert 'roc_auc' in result.metrics

    def test_handles_imbalanced_classes(self):
        """Verify behavior with highly imbalanced classes."""
        X = pd.DataFrame({
            'wiener': np.random.rand(100),
            'balaban': np.random.rand(100),
            'zagreb': np.random.rand(100)
        })
        # 95% class 0, 5% class 1
        y = np.array([0] * 95 + [1] * 5)
        
        result = train_binary_classification_fallback(X, y)
        
        assert isinstance(result, ModelResult)
        assert result.is_success is True

    def test_predict_proba_available(self, degenerate_data):
        """Verify probability predictions are available."""
        X, y = degenerate_data
        result = train_binary_classification_fallback(X, y)
        
        assert hasattr(result, 'predict_proba_available')
        assert result.predict_proba_available is True


class TestModelingUtilities:
    """Tests for utility functions in modeling.py."""

    @pytest.fixture
    def sample_features(self):
        """Sample feature matrix for VIF calculation."""
        return pd.DataFrame({
            'wiener': [10, 20, 30, 40, 50],
            'balaban': [2, 4, 6, 8, 10],
            'zagreb': [5, 10, 15, 20, 25]
        })

    def test_vif_calculation(self, sample_features):
        """Verify VIF calculation returns expected structure."""
        vif_result = calculate_vif(sample_features)
        
        assert isinstance(vif_result, pd.DataFrame)
        assert 'Feature' in vif_result.columns
        assert 'VIF' in vif_result.columns
        assert len(vif_result) == len(sample_features.columns)

    def test_degenerate_target_detection(self):
        """Verify degenerate target detection logic."""
        # Low variance target
        y_low_var = np.array([1, 1, 1, 1, 1])
        assert detect_degenerate_target(y_low_var) is True

        # High variance target
        y_high_var = np.array([1, 5, 10, 15, 20])
        assert detect_degenerate_target(y_high_var) is False

        # Empty array
        with pytest.raises((ValueError, IndexError)):
            detect_degenerate_target(np.array([]))