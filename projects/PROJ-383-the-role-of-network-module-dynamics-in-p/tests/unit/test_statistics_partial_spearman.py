"""
Unit tests for partial Spearman correlation with motion control.

Tests for code/analysis/statistics.py:
- Verify partial correlation calculation controls for motion (mean FD)
- Verify output is within valid correlation range [-1, 1]
- Verify NaN handling for invalid inputs
- Verify statistical significance calculation
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.statistics import (
    partial_spearman_correlation,
    compute_partial_correlation_matrix,
    validate_correlation_inputs
)


class TestPartialSpearmanCorrelation:
    """Tests for partial_spearman_correlation function"""

    def test_partial_correlation_basic(self):
        """Test basic partial correlation calculation with motion control"""
        # Create sample data
        np.random.seed(42)
        n_subjects = 50

        # Flexibility scores (simulated)
        flexibility = np.random.normal(0.5, 0.1, n_subjects)

        # Working memory accuracy (simulated)
        wm_accuracy = 0.6 + 0.3 * flexibility + np.random.normal(0, 0.05, n_subjects)

        # Motion parameters (mean FD) - should be controlled for
        mean_fd = np.random.normal(0.15, 0.05, n_subjects)

        # Calculate partial correlation
        rho, p_value = partial_spearman_correlation(
            flexibility,
            wm_accuracy,
            control_vars=mean_fd
        )

        # Verify correlation is in valid range
        assert -1.0 <= rho <= 1.0, f"Correlation {rho} outside valid range [-1, 1]"

        # Verify p-value is in valid range
        assert 0.0 <= p_value <= 1.0, f"P-value {p_value} outside valid range [0, 1]"

        # Verify we get a positive correlation (by construction)
        assert rho > 0, f"Expected positive correlation, got {rho}"

    def test_partial_correlation_with_no_control(self):
        """Test correlation without control variables"""
        np.random.seed(42)
        n_subjects = 30

        x = np.random.normal(0, 1, n_subjects)
        y = 0.5 * x + np.random.normal(0, 0.1, n_subjects)

        rho, p_value = partial_spearman_correlation(x, y)

        assert -1.0 <= rho <= 1.0
        assert 0.0 <= p_value <= 1.0

    def test_partial_correlation_nan_handling(self):
        """Test that NaN values are properly handled"""
        np.random.seed(42)
        n_subjects = 20

        flexibility = np.random.normal(0.5, 0.1, n_subjects)
        wm_accuracy = 0.6 + 0.3 * flexibility + np.random.normal(0, 0.05, n_subjects)
        mean_fd = np.random.normal(0.15, 0.05, n_subjects)

        # Introduce NaN values
        flexibility[5] = np.nan
        mean_fd[10] = np.nan

        # Should raise ValueError for NaN in control variables
        with pytest.raises(ValueError) as exc_info:
            partial_spearman_correlation(flexibility, wm_accuracy, control_vars=mean_fd)

        assert "NaN values" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_partial_correlation_unequal_lengths(self):
        """Test that unequal array lengths raise an error"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 2, 3, 4, 5, 6])
        control = np.array([1, 2, 3, 4, 5])

        with pytest.raises(ValueError) as exc_info:
            partial_spearman_correlation(x, y, control_vars=control)

        assert "length" in str(exc_info.value).lower()

    def test_partial_correlation_single_value(self):
        """Test that single values raise an error"""
        x = np.array([1.0])
        y = np.array([2.0])
        control = np.array([0.5])

        with pytest.raises(ValueError) as exc_info:
            partial_spearman_correlation(x, y, control_vars=control)

        assert "sample size" in str(exc_info.value).lower() or "minimum" in str(exc_info.value).lower()

    def test_partial_correlation_constant_variable(self):
        """Test handling of constant variables"""
        x = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        control = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        # Should raise error or return NaN for constant variable
        rho, p_value = partial_spearman_correlation(x, y, control_vars=control)

        # Either raises error or returns NaN
        assert np.isnan(rho) or np.isnan(p_value) or "constant" in str(ValueError).lower()

    def test_partial_correlation_motion_control_effect(self):
        """Test that controlling for motion changes the correlation"""
        np.random.seed(42)
        n_subjects = 100

        # Create correlated variables where motion is a confound
        motion = np.random.normal(0.15, 0.05, n_subjects)

        # Flexibility influenced by motion
        flexibility = 0.5 + 0.4 * motion + np.random.normal(0, 0.05, n_subjects)

        # WM accuracy influenced by motion and flexibility
        wm_accuracy = 0.5 + 0.3 * motion + 0.2 * flexibility + np.random.normal(0, 0.05, n_subjects)

        # Calculate without controlling for motion
        rho_no_control, _ = partial_spearman_correlation(flexibility, wm_accuracy)

        # Calculate with controlling for motion
        rho_with_control, _ = partial_spearman_correlation(
            flexibility,
            wm_accuracy,
            control_vars=motion
        )

        # The correlations should be different
        assert rho_no_control != rho_with_control, "Motion control should change correlation"

        # The correlation with control should be smaller (motion was a confound)
        assert abs(rho_with_control) <= abs(rho_no_control), "Controlling for confound should reduce correlation"


class TestComputePartialCorrelationMatrix:
    """Tests for compute_partial_correlation_matrix function"""

    def test_matrix_structure(self):
        """Test that the correlation matrix has correct structure"""
        np.random.seed(42)
        n_subjects = 50

        # Create sample data
        flexibility = np.random.normal(0.5, 0.1, n_subjects)
        wm_accuracy = 0.6 + 0.3 * flexibility + np.random.normal(0, 0.05, n_subjects)
        mean_fd = np.random.normal(0.15, 0.05, n_subjects)

        # Create DataFrame
        data = pd.DataFrame({
            'flexibility': flexibility,
            'wm_accuracy': wm_accuracy,
            'mean_fd': mean_fd
        })

        # Calculate partial correlation matrix
        corr_matrix, p_matrix = compute_partial_correlation_matrix(
            data,
            target_col='wm_accuracy',
            control_cols=['mean_fd']
        )

        # Verify matrix structure
        assert isinstance(corr_matrix, pd.DataFrame)
        assert isinstance(p_matrix, pd.DataFrame)

        # Verify indices and columns
        assert 'flexibility' in corr_matrix.columns
        assert 'flexibility' in corr_matrix.index

    def test_matrix_diagonal(self):
        """Test that diagonal elements are 1.0"""
        np.random.seed(42)
        n_subjects = 30

        data = pd.DataFrame({
            'var1': np.random.normal(0, 1, n_subjects),
            'var2': np.random.normal(0, 1, n_subjects),
            'control': np.random.normal(0, 1, n_subjects)
        })

        corr_matrix, p_matrix = compute_partial_correlation_matrix(
            data,
            target_col='var1',
            control_cols=['control']
        )

        # Diagonal should be 1.0
        assert abs(corr_matrix.loc['var1', 'var1'] - 1.0) < 1e-10


class TestValidateCorrelationInputs:
    """Tests for validate_correlation_inputs function"""

    def test_valid_inputs(self):
        """Test validation with valid inputs"""
        np.random.seed(42)
        n_subjects = 50

        x = np.random.normal(0, 1, n_subjects)
        y = np.random.normal(0, 1, n_subjects)
        control = np.random.normal(0, 1, n_subjects)

        # Should not raise
        result = validate_correlation_inputs(x, y, control_vars=control)
        assert result is True

    def test_invalid_input_types(self):
        """Test validation with invalid input types"""
        x = [1, 2, 3, 4, 5]  # List instead of array
        y = np.array([1, 2, 3, 4, 5])

        with pytest.raises((TypeError, ValueError)):
            validate_correlation_inputs(x, y)

    def test_insufficient_sample_size(self):
        """Test validation with too few samples"""
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        control = np.array([0.5, 0.6])

        with pytest.raises(ValueError) as exc_info:
            validate_correlation_inputs(x, y, control_vars=control)

        assert "sample" in str(exc_info.value).lower() or "minimum" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])