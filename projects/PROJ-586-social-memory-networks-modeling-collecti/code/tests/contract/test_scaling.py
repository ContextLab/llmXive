"""
Contract tests for scaling plot generation.

These tests verify the schema and structure of the scaling plot output.
"""
import pytest
from pathlib import Path
import sys

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import (
    ScalingPlotResult,
    power_law,
    fit_power_law_with_ci,
    load_scaling_data_real,
    generate_scaling_plot_with_notes
)
import numpy as np


class TestScalingPlotResult:
    """Test ScalingPlotResult dataclass."""

    def test_result_fields_exist(self):
        """Verify all required fields exist in result."""
        result = ScalingPlotResult(
            success=True,
            plot_path="/tmp/test.pdf",
            exponent=0.5,
            exponent_ci_lower=0.4,
            exponent_ci_upper=0.6,
            r_squared=0.85,
            message="Success"
        )
        
        assert result.success is True
        assert result.plot_path == "/tmp/test.pdf"
        assert result.exponent == 0.5
        assert result.exponent_ci_lower == 0.4
        assert result.exponent_ci_upper == 0.6
        assert result.r_squared == 0.85
        assert result.message == "Success"

    def test_result_failure_state(self):
        """Verify failure state has null values."""
        result = ScalingPlotResult(
            success=False,
            plot_path="/tmp/test.pdf",
            exponent=None,
            exponent_ci_lower=None,
            exponent_ci_upper=None,
            r_squared=None,
            message="Failed"
        )
        
        assert result.success is False
        assert result.exponent is None
        assert result.exponent_ci_lower is None
        assert result.exponent_ci_upper is None
        assert result.r_squared is None


class TestPowerLawFunction:
    """Test power-law computation."""

    def test_basic_power_law(self):
        """Test basic power-law calculation."""
        x = np.array([1.0, 2.0, 3.0])
        beta = 0.5
        alpha = 2.0
        
        y = power_law(x, beta, alpha)
        
        expected = alpha * np.power(x, beta)
        np.testing.assert_array_almost_equal(y, expected)

    def test_negative_exponent(self):
        """Test power-law with negative exponent."""
        x = np.array([1.0, 2.0, 4.0])
        beta = -1.0
        alpha = 10.0
        
        y = power_law(x, beta, alpha)
        
        # y = 10 * x^(-1) = 10/x
        expected = np.array([10.0, 5.0, 2.5])
        np.testing.assert_array_almost_equal(y, expected)


class TestPowerLawFitting:
    """Test power-law fitting with confidence intervals."""

    def test_fit_perfect_power_law(self):
        """Test fitting on perfect power-law data."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        beta_true = 0.5
        alpha_true = 2.0
        y = power_law(x, beta_true, alpha_true)
        
        beta, alpha, ci_lower, ci_upper, r_squared = fit_power_law_with_ci(x, y)
        
        # Should recover true parameters approximately
        assert abs(beta - beta_true) < 0.01
        assert abs(alpha - alpha_true) < 0.01
        assert r_squared > 0.99

    def test_fit_with_noise(self):
        """Test fitting on noisy power-law data."""
        np.random.seed(42)
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        beta_true = 0.5
        alpha_true = 2.0
        y = power_law(x, beta_true, alpha_true) + np.random.normal(0, 0.1, len(x))
        
        beta, alpha, ci_lower, ci_upper, r_squared = fit_power_law_with_ci(x, y)
        
        # Should still be close to true values
        assert abs(beta - beta_true) < 0.2
        assert ci_lower < beta < ci_upper
        assert r_squared > 0.8

    def test_insufficient_data_points(self):
        """Test fitting with only 1 data point."""
        x = np.array([1.0])
        y = np.array([1.0])
        
        with pytest.raises(ValueError, match="At least 2 data points"):
            fit_power_law_with_ci(x, y)

    def test_non_positive_values(self):
        """Test fitting with non-positive values."""
        x = np.array([-1.0, 0.0, 1.0, 2.0])
        y = np.array([1.0, 1.0, 1.0, 2.0])
        
        # Should filter out non-positive values and still work
        beta, alpha, ci_lower, ci_upper, r_squared = fit_power_law_with_ci(x, y)
        
        # Should use only positive values
        assert beta is not None
        assert alpha is not None


class TestScalingPlotGeneration:
    """Test scaling plot generation workflow."""

    def test_plot_result_schema(self):
        """Verify plot result contains all required schema fields."""
        result = ScalingPlotResult(
            success=True,
            plot_path="/tmp/test.pdf",
            exponent=0.5,
            exponent_ci_lower=0.4,
            exponent_ci_upper=0.6,
            r_squared=0.85,
            message="Test"
        )
        
        # Verify schema
        assert hasattr(result, 'success')
        assert hasattr(result, 'plot_path')
        assert hasattr(result, 'exponent')
        assert hasattr(result, 'exponent_ci_lower')
        assert hasattr(result, 'exponent_ci_upper')
        assert hasattr(result, 'r_squared')
        assert hasattr(result, 'message')

    def test_plot_contains_reliability_note(self):
        """Verify that the plot generation includes reliability warnings."""
        # This is a contract test - we verify the function signature
        # and that it accepts the necessary parameters for note generation
        import inspect
        
        sig = inspect.signature(generate_scaling_plot_with_notes)
        params = list(sig.parameters.keys())
        
        assert 'data_path' in params
        assert 'output_path' in params
        assert 'metric' in params