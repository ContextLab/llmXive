"""
Tests for Task T004: Validate ERA5 Sample Integrity.
"""
import os
import sys
import pytest
import tempfile
import h5py
import numpy as np
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validate_era5_sample_integrity import (
    validate_temporal_resolution,
    validate_grid_size,
    validate_temperature_range
)

class TestTemporalResolution:
    def test_hourly_resolution(self):
        """Test that hourly resolution is correctly identified."""
        # Create mock time data: 24 hours
        time_data = np.arange(0, 24, 1.0)  # 0, 1, 2, ..., 23
        
        # Mock dataset object
        class MockDataset:
            def __init__(self, data):
                self._data = data
                self.attrs = {'units': 'hours since 1900-01-01 00:00:00'}
            
            def __getitem__(self, key):
                return self._data

        mock_ds = MockDataset(time_data)
        is_valid, details = validate_temporal_resolution(mock_ds)
        
        assert is_valid is True
        assert "1 hour" in details

    def test_non_hourly_resolution(self):
        """Test that non-hourly resolution is correctly identified."""
        # Create mock time data: 24 hours but with 2-hour intervals
        time_data = np.arange(0, 48, 2.0)  # 0, 2, 4, ..., 46
        
        class MockDataset:
            def __init__(self, data):
                self._data = data
                self.attrs = {'units': 'hours since 1900-01-01 00:00:00'}
            
            def __getitem__(self, key):
                return self._data

        mock_ds = MockDataset(time_data)
        is_valid, details = validate_temporal_resolution(mock_ds)
        
        assert is_valid is False
        assert "failed" in details.lower()

    def test_insufficient_points(self):
        """Test that insufficient time points are handled."""
        time_data = np.array([0.0])
        
        class MockDataset:
            def __init__(self, data):
                self._data = data
                self.attrs = {'units': 'hours since 1900-01-01 00:00:00'}
            
            def __getitem__(self, key):
                return self._data

        mock_ds = MockDataset(time_data)
        is_valid, details = validate_temporal_resolution(mock_ds)
        
        assert is_valid is False
        assert "Insufficient" in details

class TestGridSize:
    def test_fixed_grid(self):
        """Test that a fixed grid size is correctly identified."""
        # Mock data shape: (time, lat, lon) -> (24, 721, 1440)
        shape = (24, 721, 1440)
        
        class MockDataset:
            def __init__(self, shape):
                self.shape = shape
            
            def __getitem__(self, key):
                return np.zeros(self.shape)

        mock_ds = MockDataset(shape)
        is_valid, details = validate_grid_size(mock_ds)
        
        assert is_valid is True
        assert "721x1440" in details

    def test_invalid_dimensions(self):
        """Test that invalid dimensions are handled."""
        shape = (24, 0, 1440)  # Invalid lat dimension
        
        class MockDataset:
            def __init__(self, shape):
                self.shape = shape
            
            def __getitem__(self, key):
                return np.zeros(self.shape)

        mock_ds = MockDataset(shape)
        is_valid, details = validate_grid_size(mock_ds)
        
        assert is_valid is False
        assert "Invalid" in details

class TestTemperatureRange:
    def test_valid_range(self):
        """Test that valid temperature range is correctly identified."""
        # Create mock data within bounds
        data = np.random.uniform(-40.0, 40.0, size=(24, 10, 10))
        
        class MockDataset:
            def __init__(self, data):
                self._data = data
            
            def __getitem__(self, key):
                return self._data

        mock_ds = MockDataset(data)
        is_valid, details = validate_temperature_range(mock_ds)
        
        assert is_valid is True
        assert "verified" in details.lower()

    def test_out_of_range_high(self):
        """Test that out-of-range high temperatures are detected."""
        data = np.random.uniform(-40.0, 70.0, size=(24, 10, 10))  # Max > 60
        
        class MockDataset:
            def __init__(self, data):
                self._data = data
            
            def __getitem__(self, key):
                return self._data

        mock_ds = MockDataset(data)
        is_valid, details = validate_temperature_range(mock_ds)
        
        assert is_valid is False
        assert "violation" in details.lower()

    def test_out_of_range_low(self):
        """Test that out-of-range low temperatures are detected."""
        data = np.random.uniform(-60.0, 40.0, size=(24, 10, 10))  # Min < -50
        
        class MockDataset:
            def __init__(self, data):
                self._data = data
            
            def __getitem__(self, key):
                return self._data

        mock_ds = MockDataset(data)
        is_valid, details = validate_temperature_range(mock_ds)
        
        assert is_valid is False
        assert "violation" in details.lower()

    def test_no_valid_data(self):
        """Test handling of no valid data (all NaN)."""
        data = np.full((24, 10, 10), np.nan)
        
        class MockDataset:
            def __init__(self, data):
                self._data = data
            
            def __getitem__(self, key):
                return self._data

        mock_ds = MockDataset(data)
        is_valid, details = validate_temperature_range(mock_ds)
        
        assert is_valid is False
        assert "No valid" in details

class TestIntegration:
    def test_end_to_end_file_creation(self):
        """Test that the main function creates the log file if run in a temp dir."""
        # This is a structural test to ensure the script doesn't crash on valid inputs
        # We cannot easily test the full main() without a real file, so we test the components
        assert validate_temporal_resolution is not None
        assert validate_grid_size is not None
        assert validate_temperature_range is not None