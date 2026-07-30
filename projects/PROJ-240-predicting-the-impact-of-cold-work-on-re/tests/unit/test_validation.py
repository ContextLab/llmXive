"""
Unit tests for physical bound validation logic.
Implements TDD: Tests are written first to define the expected behavior.
"""
import pytest
import pandas as pd
import numpy as np
from utils import validate_physical_bounds

class TestPhysicalBoundsValidation:
    """Tests for the validate_physical_bounds function."""

    def test_valid_data_passes(self):
        """Test that data within physical bounds returns True for all rows."""
        data = pd.DataFrame({
            'cold_work': [10.0, 50.0, 90.0],
            'time_to_peak': [100.0, 200.0, 300.0],
            'temperature': [300.0, 350.0, 400.0]
        })
        result = validate_physical_bounds(data)
        assert result.all(), "All valid rows should pass validation."
        assert len(result) == 3

    def test_cold_work_below_zero_fails(self):
        """Test that negative cold work values are flagged as invalid."""
        data = pd.DataFrame({
            'cold_work': [-5.0, 20.0, 50.0],
            'time_to_peak': [100.0, 200.0, 300.0],
            'temperature': [300.0, 350.0, 400.0]
        })
        result = validate_physical_bounds(data)
        assert result.iloc[0] is False, "Negative cold work should fail."
        assert result.iloc[1] is True
        assert result.iloc[2] is True

    def test_cold_work_above_100_fails(self):
        """Test that cold work > 100% is flagged as invalid."""
        data = pd.DataFrame({
            'cold_work': [10.0, 105.0, 50.0],
            'time_to_peak': [100.0, 200.0, 300.0],
            'temperature': [300.0, 350.0, 400.0]
        })
        result = validate_physical_bounds(data)
        assert result.iloc[0] is True
        assert result.iloc[1] is False, "Cold work > 100% should fail."
        assert result.iloc[2] is True

    def test_negative_time_fails(self):
        """Test that negative time_to_peak values are flagged as invalid."""
        data = pd.DataFrame({
            'cold_work': [20.0, 50.0, 80.0],
            'time_to_peak': [-10.0, 200.0, 300.0],
            'temperature': [300.0, 350.0, 400.0]
        })
        result = validate_physical_bounds(data)
        assert result.iloc[0] is False, "Negative time should fail."
        assert result.iloc[1] is True
        assert result.iloc[2] is True

    def test_zero_time_fails(self):
        """Test that zero time_to_peak is considered invalid (must be positive)."""
        data = pd.DataFrame({
            'cold_work': [20.0, 50.0, 80.0],
            'time_to_peak': [0.0, 200.0, 300.0],
            'temperature': [300.0, 350.0, 400.0]
        })
        result = validate_physical_bounds(data)
        assert result.iloc[0] is False, "Zero time should fail."
        assert result.iloc[1] is True

    def test_zero_cold_work_is_valid(self):
        """Test that zero cold work is valid (representing annealed state)."""
        data = pd.DataFrame({
            'cold_work': [0.0, 50.0, 100.0],
            'time_to_peak': [100.0, 200.0, 300.0],
            'temperature': [300.0, 350.0, 400.0]
        })
        result = validate_physical_bounds(data)
        assert result.all(), "Zero cold work is physically valid."

    def test_edge_case_100_cold_work(self):
        """Test that exactly 100% cold work is valid."""
        data = pd.DataFrame({
            'cold_work': [100.0],
            'time_to_peak': [100.0],
            'temperature': [300.0]
        })
        result = validate_physical_bounds(data)
        assert result.iloc[0] is True, "100% cold work should be valid."

    def test_empty_dataframe(self):
        """Test behavior with an empty DataFrame."""
        data = pd.DataFrame(columns=['cold_work', 'time_to_peak', 'temperature'])
        result = validate_physical_bounds(data)
        assert len(result) == 0, "Empty input should return empty boolean series."

    def test_missing_columns_raises_error(self):
        """Test that missing required columns raises a KeyError."""
        data = pd.DataFrame({
            'cold_work': [20.0],
            'temperature': [300.0]
            # 'time_to_peak' is missing
        })
        with pytest.raises(KeyError):
            validate_physical_bounds(data)

    def test_nan_values_fail_validation(self):
        """Test that NaN values in critical columns fail validation."""
        data = pd.DataFrame({
            'cold_work': [np.nan, 50.0],
            'time_to_peak': [100.0, 200.0],
            'temperature': [300.0, 350.0]
        })
        result = validate_physical_bounds(data)
        assert result.iloc[0] is False, "NaN cold work should fail."
        assert result.iloc[1] is True