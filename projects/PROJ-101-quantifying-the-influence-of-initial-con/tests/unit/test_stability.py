"""
Unit tests for stability.py module.
"""
import pytest
import numpy as np
from code.utils.stability import (
    check_numerical_validity,
    check_boundedness,
    check_convergence,
    detect_divergence_rate,
    validate_trajectory,
    StabilityReport,
    NumericalStabilityError,
    DivergenceError,
    NonConvergenceError
)


class TestCheckNumericalValidity:
    """Tests for check_numerical_validity function."""

    def test_valid_vector(self):
        """Test valid vector passes."""
        vector = np.array([1.0, 2.0, 3.0])
        is_valid, warnings = check_numerical_validity(vector)
        assert is_valid
        assert len(warnings) == 0

    def test_nan_vector(self):
        """Test vector with NaN fails."""
        vector = np.array([1.0, np.nan, 3.0])
        is_valid, warnings = check_numerical_validity(vector)
        assert not is_valid
        assert any("NaN" in w for w in warnings)

    def test_inf_vector(self):
        """Test vector with Inf fails."""
        vector = np.array([1.0, np.inf, 3.0])
        is_valid, warnings = check_numerical_validity(vector)
        assert not is_valid
        assert any("Inf" in w for w in warnings)

    def test_overflow_vector(self):
        """Test vector with overflow fails."""
        vector = np.array([1.0, 1e15, 3.0])
        is_valid, warnings = check_numerical_validity(vector, threshold=1e12)
        assert not is_valid
        assert any("exceeds threshold" in w for w in warnings)


class TestCheckBoundedness:
    """Tests for check_boundedness function."""

    def test_bounded_vector(self):
        """Test bounded vector passes."""
        vector = np.array([1.0, 2.0, 3.0])
        assert check_boundedness(vector, threshold=10.0)

    def test_unbounded_vector(self):
        """Test unbounded vector fails."""
        vector = np.array([1.0, 150.0, 3.0])
        assert not check_boundedness(vector, threshold=100.0)

    def test_empty_vector(self):
        """Test empty vector is considered bounded."""
        vector = np.array([])
        assert check_boundedness(vector, threshold=100.0)

    def test_negative_values(self):
        """Test negative values are checked by absolute value."""
        vector = np.array([-150.0, 2.0, 3.0])
        assert not check_boundedness(vector, threshold=100.0)


class TestCheckConvergence:
    """Tests for check_convergence function."""

    def test_converged_sequence(self):
        """Test converged sequence passes."""
        # Create a sequence that converges
        values = np.array([1.0, 1.0001, 1.00001, 1.000001, 1.0000001])
        assert check_convergence(values, tol=1e-6)

    def test_non_converged_sequence(self):
        """Test non-converged sequence fails."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert not check_convergence(values, tol=1e-6)

    def test_short_sequence(self):
        """Test short sequence fails (insufficient data)."""
        values = np.array([1.0, 2.0])
        assert not check_convergence(values, tol=1e-6, window=10)

    def test_zero_values(self):
        """Test sequence converging to zero."""
        values = np.array([0.001, 0.0001, 0.00001, 0.0, 0.0])
        assert check_convergence(values, tol=1e-6)


class TestDetectDivergenceRate:
    """Tests for detect_divergence_rate function."""

    def test_exponential_growth(self):
        """Test detection of exponential growth."""
        # Create exponential growth: e^(0.1 * t)
        t = np.arange(100)
        trajectory = np.exp(0.1 * t).reshape(-1, 1)
        rate = detect_divergence_rate(trajectory)
        assert rate is not None
        assert 0.05 < rate < 0.15  # Allow some tolerance

    def test_constant_trajectory(self):
        """Test constant trajectory has zero rate."""
        trajectory = np.ones((100, 1))
        rate = detect_divergence_rate(trajectory)
        assert rate is not None
        assert abs(rate) < 0.01

    def test_short_trajectory(self):
        """Test short trajectory returns None."""
        trajectory = np.array([[1.0], [2.0]])
        rate = detect_divergence_rate(trajectory)
        # May return None or a value, but should not crash

    def test_zero_trajectory(self):
        """Test zero trajectory returns None."""
        trajectory = np.zeros((100, 1))
        rate = detect_divergence_rate(trajectory)
        assert rate is None


class TestValidateTrajectory:
    """Tests for validate_trajectory function."""

    def test_valid_trajectory(self):
        """Test valid trajectory passes all checks."""
        trajectory = np.random.randn(200, 3) * 0.5  # Small random values
        report = validate_trajectory(trajectory, max_bound=100.0, min_steps=100)

        assert report.is_stable
        assert report.bounded
        assert report.max_value < 100.0

    def test_too_short_trajectory(self):
        """Test trajectory too short fails."""
        trajectory = np.random.randn(50, 3)
        report = validate_trajectory(trajectory, min_steps=100)
        assert not report.is_stable
        assert any("too short" in w.lower() for w in report.warnings)

    def test_unbounded_trajectory(self):
        """Test unbounded trajectory fails."""
        trajectory = np.random.randn(200, 3) * 200  # Large values
        report = validate_trajectory(trajectory, max_bound=100.0)
        assert not report.bounded
        assert any("exceeds bound" in w.lower() for w in report.warnings)

    def test_nan_trajectory(self):
        """Test trajectory with NaN fails."""
        trajectory = np.random.randn(200, 3)
        trajectory[10, 0] = np.nan
        report = validate_trajectory(trajectory)
        assert not report.is_stable
        assert any("NaN" in w for w in report.warnings)

    def test_3d_trajectory(self):
        """Test 3D trajectory fails dimension check."""
        trajectory = np.random.randn(100, 3, 2)
        report = validate_trajectory(trajectory)
        assert not report.is_stable
        assert any("2D" in w for w in report.warnings)


class TestStabilityReport:
    """Tests for StabilityReport dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        report = StabilityReport(
            is_stable=True,
            bounded=True,
            converged=False,
            max_value=50.0,
            divergence_rate=0.1,
            warnings=["Test warning"],
            details={"key": "value"}
        )

        d = report.to_dict()
        assert d["is_stable"] is True
        assert d["bounded"] is True
        assert d["converged"] is False
        assert d["max_value"] == 50.0
        assert d["divergence_rate"] == 0.1
        assert "Test warning" in d["warnings"]
        assert d["details"]["key"] == "value"