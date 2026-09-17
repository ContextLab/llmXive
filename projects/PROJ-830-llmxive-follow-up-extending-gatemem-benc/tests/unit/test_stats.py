"""
Unit tests for statistical primitives in code/utils/stats.py.
"""

import pytest
import numpy as np
import pandas as pd
from code.utils.stats import (
    shapiro_wilk_test,
    fit_fixed_effects_glm,
    run_mcnemar_test
)


class TestStatPrimitives:
    """Tests for the statistical primitive functions."""

    def test_shapiro_wilk_test_normal_data(self):
        """Test Shapiro-Wilk on normally distributed data."""
        # Generate normal data
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=100)

        result = shapiro_wilk_test(data)

        assert 'p_value' in result
        assert 'test_statistic' in result
        assert result['method'] == 'Shapiro-Wilk'
        assert 'is_normal' in result
        assert isinstance(result['p_value'], float)
        assert isinstance(result['test_statistic'], float)

        # For normal data, p-value should typically be > 0.05
        # (though not guaranteed, it's a reasonable check for synthetic data)
        assert result['test_statistic'] > 0.9  # W statistic close to 1 for normal

    def test_shapiro_wilk_test_non_normal_data(self):
        """Test Shapiro-Wilk on exponentially distributed data."""
        # Generate non-normal data
        np.random.seed(42)
        data = np.random.exponential(scale=1.0, size=100)

        result = shapiro_wilk_test(data)

        assert result['method'] == 'Shapiro-Wilk'
        # Exponential data is likely non-normal
        assert result['is_normal'] == False or result['p_value'] < 0.05

    def test_shapiro_wilk_test_insufficient_data(self):
        """Test Shapiro-Wilk with too few data points."""
        with pytest.raises(ValueError):
            shapiro_wilk_test([1.0, 2.0])  # Only 2 points

    def test_fit_fixed_effects_glm_basic(self):
        """Test Fixed-Effects GLM with basic data."""
        # Create synthetic data
        np.random.seed(42)
        n = 200
        df = pd.DataFrame({
            'score': np.random.normal(0.5, 0.2, n),
            'method': np.random.choice(['Gatekeeper', 'Baseline'], n),
            'Domain': np.random.choice(['medical', 'office', 'education', 'household'], n)
        })

        result = fit_fixed_effects_glm(df)

        assert 'p_value' in result
        assert 'test_statistic' in result
        assert result['method'] == 'Fixed-Effects GLM'
        assert 'converged' in result
        assert 'coefficients' in result
        assert isinstance(result['p_value'], float)
        assert isinstance(result['test_statistic'], float)

    def test_fit_fixed_effects_glm_missing_columns(self):
        """Test GLM with missing required columns."""
        df = pd.DataFrame({
            'score': [1, 2, 3],
            'method': ['A', 'B', 'A']
        })

        with pytest.raises(ValueError):
            fit_fixed_effects_glm(df)

    def test_mcnemar_test_basic(self):
        """Test McNemar's test with a standard contingency table."""
        # Example table:
        # [[10, 5],  -> 10 both correct, 5 method1 correct only
        #  [3, 20]]   -> 3 method2 correct only, 20 both incorrect
        table = [[10, 5], [3, 20]]

        result = run_mcnemar_test(table)

        assert 'p_value' in result
        assert 'test_statistic' in result
        assert result['method'] == "McNemar's Test"
        assert 'significant' in result
        assert isinstance(result['p_value'], float)
        assert isinstance(result['test_statistic'], float)

    def test_mcnemar_test_zero_discordant(self):
        """Test McNemar's test with zero discordant pairs."""
        # [[10, 0], [0, 20]] -> No discordant pairs
        table = [[10, 0], [0, 20]]

        result = run_mcnemar_test(table)

        assert result['p_value'] == 1.0
        assert result['test_statistic'] == 0.0
        assert result['significant'] == False
        assert 'note' in result

    def test_mcnemar_test_invalid_shape(self):
        """Test McNemar's test with invalid table shape."""
        with pytest.raises(ValueError):
            run_mcnemar_test([[1, 2, 3], [4, 5, 6]])  # 2x3 table
