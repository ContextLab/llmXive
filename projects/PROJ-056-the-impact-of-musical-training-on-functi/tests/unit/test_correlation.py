"""
Unit tests for correlation (Pearson/Spearman) calculation in code/analysis/correlation.py.
Implements T032: Unit test for correlation (Pearson/Spearman) calculation.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

# Import the implementation module.
# The task T035 will create this module, but we define the expected interface here
# to ensure the test is valid once T035 is implemented.
# If the module doesn't exist yet, we skip the import in a real run, but for this
# unit test generation, we assume the implementation follows the pattern of stats.py.
# We will mock the import if necessary or assume it exists for the test structure.
try:
    from analysis.correlation import (
        calculate_pearson_correlation,
        calculate_spearman_correlation,
        calculate_correlation_ci,
        process_correlation_results
    )
    CORRELATION_MODULE_AVAILABLE = True
except ImportError:
    CORRELATION_MODULE_AVAILABLE = False


class TestCorrelationCalculations:
    """Tests for correlation calculation functions."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample data for correlation testing."""
        np.random.seed(42)
        n = 50
        # Create a dataset with a known positive correlation
        x = np.random.normal(0, 1, n)
        y = 2 * x + np.random.normal(0, 0.5, n)  # Strong positive correlation
        return pd.DataFrame({
            'variable_x': x,
            'variable_y': y,
            'subject_id': [f'sub_{i}' for i in range(n)]
        })

    @pytest.fixture
    def sample_data_no_correlation(self):
        """Generate sample data with no correlation."""
        np.random.seed(123)
        n = 50
        x = np.random.normal(0, 1, n)
        y = np.random.normal(0, 1, n)  # Independent variables
        return pd.DataFrame({
            'variable_x': x,
            'variable_y': y,
            'subject_id': [f'sub_{i}' for i in range(n)]
        })

    @pytest.mark.skipif(not CORRELATION_MODULE_AVAILABLE, reason="Correlation module not yet implemented")
    def test_pearson_correlation_positive(self, sample_data):
        """Test Pearson correlation calculation with known positive correlation."""
        r, p = calculate_pearson_correlation(sample_data['variable_x'], sample_data['variable_y'])
        
        # Assert correlation is positive and significant
        assert r > 0.5, f"Expected positive correlation > 0.5, got {r}"
        assert p < 0.05, f"Expected p-value < 0.05, got {p}"
        
        # Verify against scipy implementation
        scipy_r, scipy_p = scipy_stats.pearsonr(sample_data['variable_x'], sample_data['variable_y'])
        assert np.isclose(r, scipy_r, atol=1e-6), f"Pearson r mismatch: {r} vs {scipy_r}"
        assert np.isclose(p, scipy_p, atol=1e-6), f"Pearson p-value mismatch: {p} vs {scipy_p}"

    @pytest.mark.skipif(not CORRELATION_MODULE_AVAILABLE, reason="Correlation module not yet implemented")
    def test_pearson_correlation_none(self, sample_data_no_correlation):
        """Test Pearson correlation calculation with no correlation."""
        r, p = calculate_pearson_correlation(
            sample_data_no_correlation['variable_x'], 
            sample_data_no_correlation['variable_y']
        )
        
        # Assert correlation is close to zero
        assert abs(r) < 0.3, f"Expected correlation near 0, got {r}"
        assert p > 0.05, f"Expected p-value > 0.05 for no correlation, got {p}"

    @pytest.mark.skipif(not CORRELATION_MODULE_AVAILABLE, reason="Correlation module not yet implemented")
    def test_spearman_correlation(self, sample_data):
        """Test Spearman rank correlation calculation."""
        rho, p = calculate_spearman_correlation(sample_data['variable_x'], sample_data['variable_y'])
        
        # Assert monotonic correlation exists
        assert rho > 0.5, f"Expected positive Spearman rho > 0.5, got {rho}"
        assert p < 0.05, f"Expected p-value < 0.05, got {p}"
        
        # Verify against scipy implementation
        scipy_rho, scipy_p = scipy_stats.spearmanr(sample_data['variable_x'], sample_data['variable_y'])
        assert np.isclose(rho, scipy_rho, atol=1e-6), f"Spearman rho mismatch: {rho} vs {scipy_rho}"
        assert np.isclose(p, scipy_p, atol=1e-6), f"Spearman p-value mismatch: {p} vs {scipy_p}"

    @pytest.mark.skipif(not CORRELATION_MODULE_AVAILABLE, reason="Correlation module not yet implemented")
    def test_correlation_ci_calculation(self, sample_data):
        """Test confidence interval calculation for correlation."""
        r, p = calculate_pearson_correlation(sample_data['variable_x'], sample_data['variable_y'])
        ci_lower, ci_upper = calculate_correlation_ci(r, len(sample_data))
        
        # CI should contain the true correlation (r)
        assert ci_lower < r < ci_upper, f"CI [{ci_lower}, {ci_upper}] does not contain r={r}"
        
        # CI width should be reasonable for n=50
        ci_width = ci_upper - ci_lower
        assert 0.1 < ci_width < 0.8, f"CI width {ci_width} is outside expected range for n=50"

    @pytest.mark.skipif(not CORRELATION_MODULE_AVAILABLE, reason="Correlation module not yet implemented")
    def test_process_correlation_results(self, sample_data):
        """Test the full pipeline of processing correlation results."""
        # Simulate a connection matrix scenario
        # In reality, this would iterate over connection pairs
        connection_id = "ROI1-ROI2"
        
        results = process_correlation_results(
            sample_data, 
            'variable_x', 
            'variable_y', 
            connection_id
        )
        
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'connection_id' in results
        assert 'r_value' in results
        assert 'p_value' in results
        assert 'ci_95_lower' in results
        assert 'ci_95_upper' in results
        
        # Verify values match individual function calls
        r, p = calculate_pearson_correlation(sample_data['variable_x'], sample_data['variable_y'])
        assert np.isclose(results['r_value'], r, atol=1e-6)
        assert np.isclose(results['p_value'], p, atol=1e-6)

    @pytest.mark.skipif(not CORRELATION_MODULE_AVAILABLE, reason="Correlation module not yet implemented")
    def test_correlation_with_nan_handling(self):
        """Test that correlation functions handle NaN values correctly."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, np.nan, 10.0])
        
        # Should raise error or handle NaNs gracefully
        # The implementation should either drop NaNs or raise a clear error
        try:
            r, p = calculate_pearson_correlation(x, y)
            # If it succeeds, it should be on the non-NaN pairs
            assert not np.isnan(r), "Result should not be NaN"
        except ValueError:
            # Or it might raise a clear error about missing data
            pass

    @pytest.mark.skipif(not CORRELATION_MODULE_AVAILABLE, reason="Correlation module not yet implemented")
    def test_correlation_edge_cases(self):
        """Test correlation with edge cases (constant values, single value)."""
        # Constant values (zero variance)
        x_const = np.array([5.0, 5.0, 5.0, 5.0])
        y_var = np.array([1.0, 2.0, 3.0, 4.0])
        
        # This should either return NaN or raise an error
        try:
            r, p = calculate_pearson_correlation(x_const, y_var)
            # If it returns a value, it should be NaN for constant x
            assert np.isnan(r) or np.isnan(p), "Correlation with constant variable should be undefined"
        except (ValueError, ZeroDivisionError):
            # Or it might raise an error
            pass

        # Single value
        x_single = np.array([1.0])
        y_single = np.array([2.0])
        
        try:
            r, p = calculate_pearson_correlation(x_single, y_single)
            assert np.isnan(r) or np.isnan(p), "Correlation with single value should be undefined"
        except (ValueError, ZeroDivisionError):
            pass

if __name__ == '__main__':
    pytest.main([__file__, '-v'])