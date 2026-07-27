"""
Unit tests for SI unit conversion and grid alignment logic.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.harmonize import (
    dynes_to_newtons, 
    micrometers_to_meters, 
    convert_to_si, 
    align_to_grid
)

class TestUnitConversion:
    def test_dynes_to_newtons_scalar(self):
        assert dynes_to_newtons(1.0) == 1e-5
        assert dynes_to_newtons(1000.0) == 1e-2

    def test_dynes_to_newtons_array(self):
        input_arr = np.array([1.0, 10.0, 100.0])
        result = dynes_to_newtons(input_arr)
        expected = np.array([1e-5, 1e-4, 1e-3])
        np.testing.assert_array_almost_equal(result, expected)

    def test_micrometers_to_meters_scalar(self):
        assert micrometers_to_meters(1.0) == 1e-6
        assert micrometers_to_meters(1000000.0) == 1.0

    def test_micrometers_to_meters_array(self):
        input_arr = np.array([1.0, 100.0, 1000.0])
        result = micrometers_to_meters(input_arr)
        expected = np.array([1e-6, 1e-4, 1e-3])
        np.testing.assert_array_almost_equal(result, expected)

class TestConvertToSi:
    def test_convert_to_si_basic(self):
        df = pd.DataFrame({
            'force_dyne': [1.0, 2.0],
            'separation_um': [10.0, 20.0]
        })
        result = convert_to_si(df)
        
        assert 'force_N' in result.columns
        assert 'separation_m' in result.columns
        assert result['force_N'].iloc[0] == 1e-5
        assert result['separation_m'].iloc[0] == 1e-5

    def test_convert_to_si_missing_columns(self):
        df = pd.DataFrame({'force_dyne': [1.0]})
        with pytest.raises(ValueError):
            convert_to_si(df)

class TestAlignToGrid:
    def test_align_linear(self):
        sep_m = np.array([1e-5, 2e-5, 3e-5])
        force_n = np.array([1.0, 2.0, 3.0])
        target = np.array([1e-5, 1.5e-5, 2e-5, 2.5e-5, 3e-5])
        
        out_sep, out_force = align_to_grid(sep_m, force_n, target)
        
        np.testing.assert_array_equal(out_sep, target)
        # Linear interpolation: 1.5e-5 should be 1.5
        assert np.isclose(out_force[1], 1.5)
        assert np.isclose(out_force[3], 2.5)

    def test_align_out_of_bounds(self):
        sep_m = np.array([1e-5, 2e-5, 3e-5])
        force_n = np.array([1.0, 2.0, 3.0])
        # Target includes points outside range
        target = np.array([0.5e-5, 1e-5, 2e-5, 4e-5])
        
        out_sep, out_force = align_to_grid(sep_m, force_n, target)
        
        # Points outside should be NaN
        assert np.isnan(out_force[0])
        assert np.isnan(out_force[3])
        # Points inside should be valid
        assert not np.isnan(out_force[1])
        assert not np.isnan(out_force[2])
