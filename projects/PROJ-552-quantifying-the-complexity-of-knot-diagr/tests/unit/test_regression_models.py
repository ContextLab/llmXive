"""
Unit tests for regression model logic.

Tests verify model initialization, fitting, and prediction logic
per FR-007 reproducibility requirements.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from analysis.regression_models import (
    KnotRegressionModel,
    ModelConfig,
    fit_model,
    evaluate_model,
    generate_predictions
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_default_config_creation(self):
        """Test ModelConfig can be created with defaults."""
        config = ModelConfig()
        assert config.model_type == "linear"
        assert config.regularization_strength == 0.0
        assert config.max_iterations == 1000

    def test_custom_config_creation(self):
        """Test ModelConfig with custom parameters."""
        config = ModelConfig(
            model_type="ridge",
            regularization_strength=0.1,
            max_iterations=500
        )
        assert config.model_type == "ridge"
        assert config.regularization_strength == 0.1
        assert config.max_iterations == 500


class TestKnotRegressionModel:
    """Tests for KnotRegressionModel class."""

    def test_model_initialization(self):
        """Test model can be initialized with config."""
        config = ModelConfig(model_type="linear")
        model = KnotRegressionModel(config)
        assert model.config.model_type == "linear"
        assert model.fitted is False

    def test_model_fit_raises_before_data(self):
        """Test that fitting without data raises error."""
        config = ModelConfig()
        model = KnotRegressionModel(config)
        with pytest.raises(ValueError):
            model.fit(np.array([]), np.array([]))

    @patch('analysis.regression_models.LinearRegression')
    def test_model_fit_success(self, mock_lr_class):
        """Test successful model fitting."""
        mock_instance = MagicMock()
        mock_instance.fit.return_value = None
        mock_instance.coef_ = np.array([1.0, 2.0])
        mock_instance.intercept_ = 0.5
        mock_lr_class.return_value = mock_instance

        config = ModelConfig()
        model = KnotRegressionModel(config)
        X = np.array([[1, 2], [3, 4]])
        y = np.array([5, 6])

        model.fit(X, y)

        assert model.fitted is True
        mock_instance.fit.assert_called_once_with(X, y)


class TestFitModel:
    """Tests for the fit_model function."""

    def test_fit_model_creates_and_returns_model(self):
        """Test fit_model instantiates and fits a model."""
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])
        config = ModelConfig(model_type="linear")

        model = fit_model(X, y, config)

        assert model is not None
        assert model.fitted is True


class TestEvaluateModel:
    """Tests for the evaluate_model function."""

    def test_evaluate_model_returns_metrics(self):
        """Test evaluate_model returns expected metrics dict."""
        config = ModelConfig()
        model = KnotRegressionModel(config)
        model.coef_ = np.array([1.0])
        model.intercept_ = 0.0
        model.fitted = True

        X = np.array([[1], [2], [3]])
        y = np.array([1, 2, 3])

        metrics = evaluate_model(model, X, y)

        assert "r2_score" in metrics
        assert "mean_squared_error" in metrics
        assert "mean_absolute_error" in metrics


class TestGeneratePredictions:
    """Tests for the generate_predictions function."""

    def test_generate_predictions_returns_array(self):
        """Test generate_predictions returns numpy array."""
        config = ModelConfig()
        model = KnotRegressionModel(config)
        model.coef_ = np.array([2.0])
        model.intercept_ = 1.0
        model.fitted = True

        X = np.array([[1], [2], [3]])
        predictions = generate_predictions(model, X)

        assert isinstance(predictions, np.ndarray)
        assert len(predictions) == 3
        assert np.allclose(predictions, [3.0, 5.0, 7.0])
