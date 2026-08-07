import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.harmonize import (
    dynes_to_newtons,
    micrometers_to_meters,
    convert_to_si,
    align_to_grid,
    construct_covariance_matrix
)

class TestUnitConversions:
    def test_dynes_to_newtons(self):
        # 1 dyne = 1e-5 N
        input_val = np.array([1.0, 100.0, 1e6])
        expected = np.array([1e-5, 1e-3, 10.0])
        result = dynes_to_newtons(input_val)
        np.testing.assert_array_almost_equal(result, expected)

    def test_micrometers_to_meters(self):
        # 1 micron = 1e-6 m
        input_val = np.array([1.0, 1000.0, 1e6])
        expected = np.array([1e-6, 1e-3, 1.0])
        result = micrometers_to_meters(input_val)
        np.testing.assert_array_almost_equal(result, expected)

class TestConvertToSI:
    def test_convert_to_si_basic(self):
        data = {
            'force': [100.0, 200.0],
            'separation': [1.0, 2.0],
            'other': ['a', 'b']
        }
        df = pd.DataFrame(data)
        result = convert_to_si(df)
        
        assert 'force_N' in result.columns
        assert 'separation_m' in result.columns
        
        # Check values
        assert result['force_N'].iloc[0] == 100.0 * 1e-5
        assert result['separation_m'].iloc[0] == 1.0 * 1e-6

    def test_convert_to_si_missing_columns(self):
        data = {'x': [1, 2], 'y': [3, 4]}
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            convert_to_si(df)

class TestAlignToGrid:
    def test_align_to_grid_basic(self):
        # Dataset 1
        df1 = pd.DataFrame({
            'separation_m': [1e-6, 2e-6, 3e-6],
            'force_N': [1.0, 2.0, 3.0]
        })
        # Dataset 2
        df2 = pd.DataFrame({
            'separation_m': [1.5e-6, 2.5e-6, 3.5e-6],
            'force_N': [1.5, 2.5, 3.5]
        })
        
        # Overlap: [1.5e-6, 3e-6]
        result_df, grid = align_to_grid([df1, df2])
        
        assert len(grid) > 0
        assert result_df['separation_m'].min() >= 1.5e-6
        assert result_df['separation_m'].max() <= 3e-6
        assert 'force_N' in result_df.columns

    def test_align_to_grid_no_overlap(self):
        df1 = pd.DataFrame({
            'separation_m': [1e-6, 2e-6],
            'force_N': [1.0, 2.0]
        })
        df2 = pd.DataFrame({
            'separation_m': [5e-6, 6e-6],
            'force_N': [5.0, 6.0]
        })
        
        with pytest.raises(ValueError, match="No overlapping separation range"):
            align_to_grid([df1, df2])

    def test_align_to_grid_interpolation(self):
        df1 = pd.DataFrame({
            'separation_m': [1e-6, 3e-6],
            'force_N': [1.0, 3.0]
        })
        
        # Custom grid
        target = np.array([2e-6])
        result_df, grid = align_to_grid([df1], target_grid=target)
        
        assert result_df['force_N'].iloc[0] == pytest.approx(2.0)

class TestConstructCovarianceMatrix:
    def test_covariance_stat_only(self):
        df = pd.DataFrame({
            'force_N': [1.0, 2.0, 3.0],
            'stat_err': [0.1, 0.2, 0.3]
        })
        cov = construct_covariance_matrix(df, stat_col='stat_err')
        
        # Diagonal should be stat^2
        expected_diag = [0.01, 0.04, 0.09]
        np.testing.assert_array_almost_equal(np.diag(cov), expected_diag)
        
        # Off-diagonal should be 0
        assert np.allclose(cov - np.diag(np.diag(cov)), 0)

    def test_covariance_stat_and_sys(self):
        df = pd.DataFrame({
            'force_N': [1.0, 2.0, 3.0],
            'stat_err': [0.1, 0.1, 0.1],
            'sys_err': [0.2, 0.2, 0.2]
        })
        cov = construct_covariance_matrix(df, stat_col='stat_err', sys_col='sys_err')
        
        # Diagonal: stat^2 + sys^2 = 0.01 + 0.04 = 0.05
        # Off-diagonal: sys^2 = 0.04
        expected_diag = [0.05, 0.05, 0.05]
        expected_off = 0.04
        
        np.testing.assert_array_almost_equal(np.diag(cov), expected_diag)
        
        for i in range(3):
            for j in range(3):
                if i != j:
                    assert cov[i, j] == pytest.approx(expected_off)
