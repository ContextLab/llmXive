import numpy as np
import pytest
from typing import Dict, Any, List

from analysis.statistics import fit_regression, fit_baseline_regression, RegressionResult


class TestFitRegression:
    """Unit tests for fit_regression and fit_baseline_regression (T051/T051b/T040)."""

    @staticmethod
    def _create_sample_data(n: int = 20) -> tuple:
        """Generate deterministic sample data for regression tests."""
        np.random.seed(42)
        flexibility = np.random.rand(n) * 0.5 + 0.1
        creativity = flexibility * 0.8 + np.random.rand(n) * 0.1 + 10.0
        age = np.random.randint(18, 65, n)
        sexes = np.random.choice(["M", "F"], n)
        education = np.random.randint(12, 21, n)
        static_strengths = np.random.rand(n) * 0.2

        return flexibility, creativity, age, sexes, education, static_strengths

    def test_fit_regression_returns_result_object(self):
        """Verify fit_regression returns a RegressionResult instance."""
        flexibility, creativity, age, sexes, education, static_strengths = (
            self._create_sample_data()
        )

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        result = fit_regression(flexibility, creativity, covariates)

        assert isinstance(result, RegressionResult)
        assert hasattr(result, "coefficients")
        assert hasattr(result, "r_squared")
        assert hasattr(result, "adjusted_r_squared")
        assert hasattr(result, "pearson_r")

    def test_fit_regression_coefficients_shape(self):
        """Verify coefficients array has expected length (intercept + 5 predictors)."""
        flexibility, creativity, age, sexes, education, static_strengths = (
            self._create_sample_data()
        )

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        result = fit_regression(flexibility, creativity, covariates)

        # 1 intercept + 5 predictors (flexibility, static, age, sex, education)
        assert len(result.coefficients) == 6

    def test_fit_regression_r_squared_in_range(self):
        """Verify R-squared is between 0 and 1."""
        flexibility, creativity, age, sexes, education, static_strengths = (
            self._create_sample_data()
        )

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        result = fit_regression(flexibility, creativity, covariates)

        assert 0.0 <= result.r_squared <= 1.0
        assert 0.0 <= result.adjusted_r_squared <= 1.0

    def test_fit_regression_pearson_r_in_range(self):
        """Verify Pearson r is between -1 and 1."""
        flexibility, creativity, age, sexes, education, static_strengths = (
            self._create_sample_data()
        )

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        result = fit_regression(flexibility, creativity, covariates)

        assert -1.0 <= result.pearson_r <= 1.0

    def test_fit_baseline_regression_excludes_flexibility(self):
        """Verify baseline model excludes network_flexibility from predictors."""
        flexibility, creativity, age, sexes, education, static_strengths = (
            self._create_sample_data()
        )

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        baseline_result = fit_baseline_regression(creativity, static_strengths, covariates)

        assert isinstance(baseline_result, RegressionResult)
        # Baseline model: intercept + static + age + sex + education = 5 coefficients
        assert len(baseline_result.coefficients) == 5

    def test_full_model_r2_greater_or_equal_baseline(self):
        """Full model should have R2 >= baseline model R2 (nested models)."""
        flexibility, creativity, age, sexes, education, static_strengths = (
            self._create_sample_data()
        )

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        full_result = fit_regression(flexibility, creativity, covariates)
        baseline_result = fit_baseline_regression(creativity, static_strengths, covariates)

        assert full_result.r_squared >= baseline_result.r_squared

    def test_fit_regression_with_constant_flexibility(self):
        """Regression should handle constant flexibility (though likely singular)."""
        n = 20
        flexibility = np.ones(n) * 0.5
        creativity = np.random.rand(n) * 10 + 5
        age = np.random.randint(18, 65, n)
        sexes = np.random.choice(["M", "F"], n)
        education = np.random.randint(12, 21, n)
        static_strengths = np.random.rand(n) * 0.2

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        # This should not crash, even if the model is singular for flexibility
        result = fit_regression(flexibility, creativity, covariates)

        assert isinstance(result, RegressionResult)

    def test_fit_regression_small_sample(self):
        """Regression should work with minimal sample size (n > number of predictors)."""
        n = 10
        flexibility = np.random.rand(n)
        creativity = flexibility * 0.5 + np.random.rand(n) * 0.1
        age = np.random.randint(18, 65, n)
        sexes = np.random.choice(["M", "F"], n)
        education = np.random.randint(12, 21, n)
        static_strengths = np.random.rand(n)

        covariates: Dict[str, Any] = {
            "static_connectivity_strength": static_strengths,
            "age": age,
            "sex": sexes,
            "education": education,
        }

        result = fit_regression(flexibility, creativity, covariates)

        assert isinstance(result, RegressionResult)
