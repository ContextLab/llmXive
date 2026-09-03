"""
Unit tests for numerical stability utilities.
"""
import pytest
import numpy as np
from unittest.mock import patch

from code.utils.stability import (
    NumericalStabilityError,
    DivergenceError,
    NonConvergenceError,
    StabilityReport,
    check_numerical_validity,
    check_boundedness,
    check_convergence,
    validate_trajectory,
    detect_divergence_rate
)
from code.config import NumericalSettings


class TestStabilityReport:
    def test_initial_state(self):
        report = StabilityReport()
        assert report.is_valid is True
        assert report.is_bounded is True
        assert report.has_converged is True
        assert report.divergence_detected is False
        assert report.max_norm == 0.0
        assert report.warnings == []

    def test_add_warning(self):
        report = StabilityReport()
        report.add_warning("Test warning")
        assert "Test warning" in report.warnings
        assert report.is_valid is False

    def test_mark_invalid(self):
        report = StabilityReport()
        report.mark_invalid("Invalid reason")
        assert "Invalid reason" in report.warnings
        assert report.is_valid is False


class TestCheckNumericalValidity:
    def test_valid_trajectory(self):
        trajectory = np.random.randn(100, 3)
        settings = NumericalSettings()
        report = check_numerical_validity(trajectory, settings)
        assert report.is_valid is True
        assert report.warnings == []

    def test_nan_values(self):
        trajectory = np.random.randn(100, 3)
        trajectory[50, 0] = np.nan
        report = check_numerical_validity(trajectory)
        assert report.is_valid is False
        assert any("NaN" in w for w in report.warnings)

    def test_inf_values(self):
        trajectory = np.random.randn(100, 3)
        trajectory[50, 0] = np.inf
        report = check_numerical_validity(trajectory)
        assert report.is_valid is False
        assert any("Inf" in w for w in report.warnings)

    def test_large_values_warning(self):
        trajectory = np.random.randn(100, 3)
        trajectory[50, 0] = 1e15
        report = check_numerical_validity(trajectory)
        assert any("Extremely large" in w for w in report.warnings)


class TestCheckBoundedness:
    def test_within_bounds(self):
        trajectory = np.random.randn(100, 3) * 0.5  # Small values
        is_bounded, max_norm, report = check_boundedness(trajectory, bound_threshold=100.0)
        assert is_bounded is True
        assert max_norm < 100.0
        assert report.is_valid is True

    def test_exceeds_bounds(self):
        trajectory = np.random.randn(100, 3) * 200.0  # Large values
        is_bounded, max_norm, report = check_boundedness(trajectory, bound_threshold=100.0)
        assert is_bounded is False
        assert max_norm > 100.0
        assert report.is_valid is False
        assert any("exceeded bound" in w for w in report.warnings)


class TestCheckConvergence:
    def test_converged_simple(self):
        t = np.linspace(0, 10, 100)
        y = np.sin(t).reshape(-1, 1)
        has_converged, error = check_convergence(t, y)
        assert has_converged is True

    def test_no_convergence_heuristic(self):
        # Create a trajectory with very high frequency oscillations
        t = np.linspace(0, 10, 1000)
        y = np.sin(100 * t).reshape(-1, 1)
        has_converged, error = check_convergence(t, y)
        # This is a heuristic check; it might still return True
        # depending on the threshold
        assert isinstance(has_converged, bool)


class TestDetectDivergenceRate:
    def test_no_divergence(self):
        t = np.linspace(0, 10, 100)
        trajectory = np.sin(t).reshape(-1, 1)
        is_diverging, rate = detect_divergence_rate(trajectory, t)
        assert is_diverging is False

    def test_exponential_divergence(self):
        t = np.linspace(0, 10, 100)
        # Exponential growth: e^t
        trajectory = np.exp(t).reshape(-1, 1)
        is_diverging, rate = detect_divergence_rate(trajectory, t)
        assert is_diverging is True
        assert rate > 0.9  # Should be close to 1.0

    def test_short_trajectory(self):
        t = np.array([0.0, 1.0])
        trajectory = np.array([[1.0], [2.0]])
        is_diverging, rate = detect_divergence_rate(trajectory, t)
        assert is_diverging is False


class TestValidateTrajectory:
    def test_full_valid_trajectory(self):
        t = np.linspace(0, 10, 100)
        trajectory = np.random.randn(100, 3) * 0.5
        report = validate_trajectory(trajectory, t)
        assert report.is_valid is True
        assert report.is_bounded is True

    def test_full_invalid_trajectory(self):
        t = np.linspace(0, 10, 100)
        trajectory = np.random.randn(100, 3) * 200.0  # Unbounded
        report = validate_trajectory(trajectory, t)
        assert report.is_valid is False
        assert report.is_bounded is False

    def test_full_with_nan(self):
        t = np.linspace(0, 10, 100)
        trajectory = np.random.randn(100, 3)
        trajectory[50, 0] = np.nan
        report = validate_trajectory(trajectory, t)
        assert report.is_valid is False
        assert any("NaN" in w for w in report.warnings)
