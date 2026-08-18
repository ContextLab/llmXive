"""
Unit tests for coupling function derivation in code/analysis/coupling_functions.py.

Tests verify:
1. Akasofu epsilon calculation (V * B_s^2 * sin^4(theta/2))
2. Newell function calculation (V^(4/3) * B_t^(2/3) * sin^8/3(theta/2))
3. Helper functions (v_bs, v_bt)
4. Edge cases (zero values, negative B_z)
"""

import pytest
import numpy as np
import pandas as pd
from analysis.coupling_functions import (
    compute_akasofu_epsilon,
    compute_newell_function,
    compute_v_bs,
    compute_v_bt,
    compute_all_coupling_functions,
    get_coupling_function_columns
)


class TestComputeVBS:
    """Tests for compute_v_bs helper function."""

    def test_positive_bs_returns_v(self):
        """When B_s is positive, should return V."""
        df = pd.DataFrame({'v_sw': [400.0], 'B_s': [5.0]})
        result = compute_v_bs(df)
        assert result.iloc[0] == 400.0

    def test_negative_bs_returns_zero(self):
        """When B_s is negative (B_z positive), should return 0."""
        df = pd.DataFrame({'v_sw': [400.0], 'B_s': [-5.0]})
        result = compute_v_bs(df)
        assert result.iloc[0] == 0.0

    def test_vectorized_positive(self):
        """Test vectorized operation with all positive B_s."""
        df = pd.DataFrame({'v_sw': [400.0, 500.0, 600.0], 'B_s': [5.0, 10.0, 15.0]})
        result = compute_v_bs(df)
        expected = pd.Series([400.0, 500.0, 600.0])
        pd.testing.assert_series_equal(result, expected)

    def test_vectorized_mixed(self):
        """Test vectorized operation with mixed B_s signs."""
        df = pd.DataFrame({'v_sw': [400.0, 500.0, 600.0], 'B_s': [5.0, -10.0, 15.0]})
        result = compute_v_bs(df)
        expected = pd.Series([400.0, 0.0, 600.0])
        pd.testing.assert_series_equal(result, expected)


class TestComputeVBT:
    """Tests for compute_v_bt helper function."""

    def test_vectorized(self):
        """Test vectorized operation."""
        df = pd.DataFrame({'v_sw': [400.0, 500.0, 600.0], 'B_t': [5.0, 10.0, 15.0]})
        result = compute_v_bt(df)
        # Just verify it runs and returns same length
        assert len(result) == 3
        assert not result.isna().any()

    def test_zero_bt(self):
        """Test with zero B_t."""
        df = pd.DataFrame({'v_sw': [400.0], 'B_t': [0.0]})
        result = compute_v_bt(df)
        assert result.iloc[0] == 0.0


class TestComputeAkasofuEpsilon:
    """Tests for Akasofu epsilon calculation."""

    def test_basic_calculation(self):
        """Test basic formula: epsilon = V * B_s^2 * sin^4(theta/2)"""
        # Use simple values where we can manually verify
        # V = 400 km/s, B_s = 5 nT, theta = 180 deg (southward IMF)
        # sin(90) = 1, so epsilon = 400 * 25 * 1 = 10000
        df = pd.DataFrame({
            'v_sw': [400.0],
            'B_s': [5.0],
            'theta': [180.0]
        })
        result = compute_akasofu_epsilon(df)
        expected = 400.0 * (5.0 ** 2) * (np.sin(np.radians(180.0 / 2)) ** 4)
        assert np.isclose(result.iloc[0], expected)

    def test_northward_imf(self):
        """When IMF is northward, B_s = 0, epsilon should be 0."""
        df = pd.DataFrame({
            'v_sw': [400.0],
            'B_s': [0.0],
            'theta': [0.0]
        })
        result = compute_akasofu_epsilon(df)
        assert result.iloc[0] == 0.0

    def test_vectorized(self):
        """Test vectorized operation."""
        df = pd.DataFrame({
            'v_sw': [400.0, 500.0, 600.0],
            'B_s': [5.0, 10.0, 0.0],
            'theta': [180.0, 180.0, 180.0]
        })
        result = compute_akasofu_epsilon(df)
        # Row 0: 400 * 25 * 1 = 10000
        # Row 1: 500 * 100 * 1 = 50000
        # Row 2: 600 * 0 * 1 = 0
        expected = [10000.0, 50000.0, 0.0]
        for i, exp in enumerate(expected):
            assert np.isclose(result.iloc[i], exp)

    def test_missing_columns_raises(self):
        """Test that missing required columns raise an error."""
        df = pd.DataFrame({'v_sw': [400.0]})
        with pytest.raises(KeyError):
            compute_akasofu_epsilon(df)


class TestComputeNewellFunction:
    """Tests for Newell function calculation."""

    def test_basic_calculation(self):
        """Test basic formula: dPhi_MP/dt = V^(4/3) * B_t^(2/3) * sin^8/3(theta/2)"""
        # V = 400, B_t = 5, theta = 180
        # sin(90) = 1
        # epsilon = 400^(4/3) * 5^(2/3) * 1
        df = pd.DataFrame({
            'v_sw': [400.0],
            'B_t': [5.0],
            'theta': [180.0]
        })
        result = compute_newell_function(df)
        expected = (400.0 ** (4/3)) * (5.0 ** (2/3)) * (np.sin(np.radians(180.0 / 2)) ** (8/3))
        assert np.isclose(result.iloc[0], expected)

    def test_zero_bt(self):
        """When B_t = 0, Newell function should be 0."""
        df = pd.DataFrame({
            'v_sw': [400.0],
            'B_t': [0.0],
            'theta': [180.0]
        })
        result = compute_newell_function(df)
        assert result.iloc[0] == 0.0

    def test_vectorized(self):
        """Test vectorized operation."""
        df = pd.DataFrame({
            'v_sw': [400.0, 500.0],
            'B_t': [5.0, 10.0],
            'theta': [180.0, 180.0]
        })
        result = compute_newell_function(df)
        assert len(result) == 2
        assert not result.isna().any()

    def test_missing_columns_raises(self):
        """Test that missing required columns raise an error."""
        df = pd.DataFrame({'v_sw': [400.0]})
        with pytest.raises(KeyError):
            compute_newell_function(df)


class TestComputeAllCouplingFunctions:
    """Tests for the combined function."""

    def test_returns_dataframe_with_columns(self):
        """Test that the function returns a DataFrame with expected columns."""
        df = pd.DataFrame({
            'v_sw': [400.0, 500.0],
            'B_s': [5.0, 10.0],
            'B_t': [5.0, 10.0],
            'theta': [180.0, 180.0]
        })
        result = compute_all_coupling_functions(df)
        
        expected_cols = ['epsilon', 'newell_function']
        for col in expected_cols:
            assert col in result.columns

    def test_values_match_individual_functions(self):
        """Test that combined function matches individual function calls."""
        df = pd.DataFrame({
            'v_sw': [400.0, 500.0, 600.0],
            'B_s': [5.0, 10.0, 0.0],
            'B_t': [5.0, 10.0, 15.0],
            'theta': [180.0, 180.0, 180.0]
        })
        
        combined = compute_all_coupling_functions(df)
        epsilon_manual = compute_akasofu_epsilon(df)
        newell_manual = compute_newell_function(df)
        
        pd.testing.assert_series_equal(combined['epsilon'], epsilon_manual)
        pd.testing.assert_series_equal(combined['newell_function'], newell_manual)

    def test_preserves_original_index(self):
        """Test that original index is preserved."""
        df = pd.DataFrame({
            'v_sw': [400.0, 500.0],
            'B_s': [5.0, 10.0],
            'B_t': [5.0, 10.0],
            'theta': [180.0, 180.0]
        }, index=[10, 20])
        
        result = compute_all_coupling_functions(df)
        assert list(result.index) == [10, 20]


class TestGetCouplingFunctionColumns:
    """Tests for column name retrieval."""

    def test_returns_expected_columns(self):
        """Test that function returns the correct column names."""
        cols = get_coupling_function_columns()
        assert 'epsilon' in cols
        assert 'newell_function' in cols
        assert len(cols) == 2

    def test_returns_list(self):
        """Test that return type is a list."""
        cols = get_coupling_function_columns()
        assert isinstance(cols, list)