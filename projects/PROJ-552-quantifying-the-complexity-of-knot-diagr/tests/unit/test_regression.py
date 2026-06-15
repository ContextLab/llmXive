"""
Unit tests for regression analysis module.

Tests goodness-of-fit metrics computation (R², AIC, BIC, MAE) and model fitting
as per FR-005.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.regression import (
    calculate_r_squared,
    calculate_aic,
    calculate_bic,
    calculate_mae,
    calculate_rmse,
    fit_linear_model,
    fit_polynomial_model,
    fit_logarithmic_model,
    compute_goodness_of_fit,
    fit_regression_models,
    RegressionMetrics,
    RegressionResult
)


class TestR_squared:
    """Tests for R² calculation."""

    def test_perfect_fit(self):
        """R² should be 1.0 for perfect fit."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        r_squared = calculate_r_squared(y_true, y_pred)

        assert r_squared == 1.0

    def test_no_correlation(self):
        """R² should be 0.0 when predictions equal mean."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([3.0, 3.0, 3.0, 3.0, 3.0])  # All predictions = mean

        r_squared = calculate_r_squared(y_true, y_pred)

        assert r_squared == pytest.approx(0.0, rel=1e-6)

    def test_negative_r_squared(self):
        """R² can be negative for poor models."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0])  # Wrong direction

        r_squared = calculate_r_squared(y_true, y_pred)

        assert r_squared < 0.0

    def test_realistic_linear_relationship(self):
        """R² should be high for realistic linear relationship with noise."""
        np.random.seed(42)
        X = np.linspace(0, 10, 100)
        y = 2 * X + 1 + np.random.normal(0, 0.5, 100)

        # Perfect linear fit
        y_pred = 2 * X + 1

        r_squared = calculate_r_squared(y, y_pred)

        assert r_squared > 0.95


class TestAIC_BIC:
    """Tests for AIC and BIC calculation."""

    def test_aic_lower_is_better(self):
        """Lower AIC indicates better model."""
        n_samples = 100
        n_parameters = 2

        # Model with lower RSS should have lower AIC
        rss_low = 10.0
        rss_high = 100.0

        aic_low = calculate_aic(n_samples, n_parameters, rss_low)
        aic_high = calculate_aic(n_samples, n_parameters, rss_high)

        assert aic_low < aic_high

    def test_bic_lower_is_better(self):
        """Lower BIC indicates better model."""
        n_samples = 100
        n_parameters = 2

        rss_low = 10.0
        rss_high = 100.0

        bic_low = calculate_bic(n_samples, n_parameters, rss_low)
        bic_high = calculate_bic(n_samples, n_parameters, rss_high)

        assert bic_low < bic_high

    def test_bic_penalizes_complexity_more(self):
        """BIC should penalize additional parameters more than AIC."""
        n_samples = 100
        rss = 50.0

        aic_2 = calculate_aic(n_samples, 2, rss)
        aic_3 = calculate_aic(n_samples, 3, rss)
        bic_2 = calculate_bic(n_samples, 2, rss)
        bic_3 = calculate_bic(n_samples, 3, rss)

        aic_penalty = aic_3 - aic_2
        bic_penalty = bic_3 - bic_2

        assert bic_penalty > aic_penalty


class TestMAE_RMSE:
    """Tests for MAE and RMSE calculation."""

    def test_mae_perfect_fit(self):
        """MAE should be 0 for perfect fit."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        mae = calculate_mae(y_true, y_pred)

        assert mae == 0.0

    def test_mae_positive_error(self):
        """MAE should be positive for imperfect fit."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.5, 2.5, 3.5, 4.5, 5.5])

        mae = calculate_mae(y_true, y_pred)

        assert mae == pytest.approx(0.5)

    def test_rmse_perfect_fit(self):
        """RMSE should be 0 for perfect fit."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        rmse = calculate_rmse(y_true, y_pred)

        assert rmse == 0.0

    def test_rmse_vs_mae(self):
        """RMSE should be >= MAE for same predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.5, 2.5, 3.5, 4.5, 5.5])

        mae = calculate_mae(y_true, y_pred)
        rmse = calculate_rmse(y_true, y_pred)

        assert rmse >= mae


class TestLinearModel:
    """Tests for linear model fitting."""

    def test_perfect_linear_data(self):
        """Should recover exact coefficients for perfect linear data."""
        X = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([3.0, 5.0, 7.0, 9.0, 11.0])  # y = 2x + 1

        coefficients, predictions = fit_linear_model(X, y)

        assert coefficients[0] == pytest.approx(1.0, rel=1e-6)  # intercept
        assert coefficients[1] == pytest.approx(2.0, rel=1e-6)  # slope

    def test_predictions_match_data(self):
        """Predictions should exactly match data for perfect linear fit."""
        X = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([3.0, 5.0, 7.0, 9.0, 11.0])

        coefficients, predictions = fit_linear_model(X, y)

        assert np.allclose(predictions, y)


class TestPolynomialModel:
    """Tests for polynomial model fitting."""

    def test_quadratic_fit(self):
        """Should fit quadratic data."""
        X = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([1.0, 4.0, 9.0, 16.0, 25.0])  # y = x²

        coefficients, predictions = fit_polynomial_model(X, y, degree=2)

        # Should have 3 coefficients (degree 2 polynomial)
        assert len(coefficients) == 3

        # Predictions should match
        assert np.allclose(predictions, y, rtol=1e-3)


class TestLogarithmicModel:
    """Tests for logarithmic model fitting."""

    def test_positive_data(self):
        """Should fit logarithmic data with positive X values."""
        X = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.log(X) * 2 + 1  # y = 2*ln(x) + 1

        coefficients, predictions = fit_logarithmic_model(X, y)

        # Should have 2 coefficients
        assert len(coefficients) == 2

    def test_non_positive_x_handling(self):
        """Should handle non-positive X values gracefully."""
        X = np.array([-1.0, 0.0, 1.0, 2.0, 3.0])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        coefficients, predictions = fit_logarithmic_model(X, y)

        # Should not crash and return valid predictions
        assert len(predictions) == len(X)
        assert not np.any(np.isnan(predictions))


class TestGoodnessOfFitMetrics:
    """Tests for complete goodness-of-fit metrics computation."""

    def test_metrics_computation(self):
        """Should compute all metrics correctly."""
        np.random.seed(42)
        X = np.linspace(0, 10, 50)
        y = 2 * X + 1 + np.random.normal(0, 0.5, 50)
        y_pred = 2 * X + 1

        metrics = compute_goodness_of_fit(y, y_pred, 'linear', 2)

        # Check all metrics are computed
        assert isinstance(metrics, RegressionMetrics)
        assert metrics.model_type == 'linear'
        assert metrics.r_squared > 0.9
        assert metrics.aic < 0  # Should be negative for good fit
        assert metrics.bic < 0
        assert metrics.mae > 0
        assert metrics.rmse > 0
        assert metrics.n_samples == 50
        assert metrics.n_parameters == 2

    def test_metrics_to_dict(self):
        """Should convert to dictionary correctly."""
        metrics = RegressionMetrics(
            model_type='linear',
            r_squared=0.95,
            aic=-100.0,
            bic=-95.0,
            mae=0.5,
            rmse=0.6,
            n_samples=50,
            n_parameters=2,
            formula='y = β₀ + β₁*x'
        )

        d = metrics.to_dict()

        assert d['model_type'] == 'linear'
        assert d['r_squared'] == 0.95
        assert 'r_squared' in d


class TestRegressionModels:
    """Tests for fitting multiple regression models."""

    def test_all_models_fitted(self):
        """Should fit all requested model types."""
        np.random.seed(42)
        X = np.linspace(1, 10, 50)
        y = 2 * X + 1 + np.random.normal(0, 0.5, 50)

        results = fit_regression_models(X, y, ['linear', 'polynomial', 'logarithmic'])

        # Should have 3 results
        assert len(results) == 3

        # Each result should have required fields
        for result in results:
            assert isinstance(result, RegressionResult)
            assert result.model_type in ['linear', 'polynomial', 'logarithmic']
            assert len(result.coefficients) > 0
            assert len(result.predictions) == len(y)
            assert len(result.residuals) == len(y)

    def test_linear_model_has_correct_coefficients(self):
        """Linear model should have correct coefficient count."""
        np.random.seed(42)
        X = np.linspace(0, 10, 50)
        y = 2 * X + 1 + np.random.normal(0, 0.5, 50)

        results = fit_regression_models(X, y, ['linear'])

        assert len(results) == 1
        assert results[0].model_type == 'linear'
        assert len(results[0].coefficients) == 2  # intercept + slope


class TestIntegration:
    """Integration tests for regression analysis."""

    def test_end_to_end_analysis(self):
        """Should run complete analysis on sample data."""
        np.random.seed(42)

        # Create sample data
        X = np.linspace(1, 13, 100)  # Crossing numbers 1-13
        y = 0.5 * X + 0.1 * X**2 + np.random.normal(0, 0.3, 100)  # Volume relationship

        results = fit_regression_models(X, y)

        # Should have results for all models
        assert len(results) > 0

        # Should have computed metrics for each
        for result in results:
            assert result.metrics.r_squared >= -1  # R² can be negative
            assert np.isfinite(result.metrics.aic)
            assert np.isfinite(result.metrics.bic)
            assert np.isfinite(result.metrics.mae)

    def test_model_comparison(self):
        """Should be able to compare models by R²."""
        np.random.seed(42)
        X = np.linspace(1, 10, 50)
        y = 2 * X + 1 + np.random.normal(0, 0.5, 50)

        results = fit_regression_models(X, y)

        # Find best model
        best_result = max(results, key=lambda r: r.metrics.r_squared)

        # Linear should be best for linear data
        assert best_result.model_type == 'linear'
        assert best_result.metrics.r_squared > 0.9


if __name__ == '__main__':
    pytest.main([__file__, '-v'])