"""
Unit tests for T012b: validate_data_availability function.
"""

import os
import tempfile
import pytest
import pandas as pd
from code.validate_data_availability import validate_data_availability


class TestDataAvailabilityValidation:
    """Tests for data availability validation logic."""

    def test_valid_dataset_size(self, tmp_path):
        """Test that a dataset with N >= 1000 passes validation."""
        # Create a mock dataset with 1000 rows
        mock_data = pd.DataFrame({
            'composition': ['Fe50Co30Ni20'] * 1000,
            'critical_cooling_rate': [100.0] * 1000
        })
        
        data_file = tmp_path / "processed_alloys_raw.csv"
        mock_data.to_csv(data_file, index=False)
        
        # Should not raise
        result = validate_data_availability(str(data_file), min_samples=1000)
        assert result is True

    def test_insufficient_dataset_size(self, tmp_path):
        """Test that a dataset with N < 1000 raises ValueError."""
        # Create a mock dataset with 999 rows
        mock_data = pd.DataFrame({
            'composition': ['Fe50Co30Ni20'] * 999,
            'critical_cooling_rate': [100.0] * 999
        })
        
        data_file = tmp_path / "processed_alloys_raw.csv"
        mock_data.to_csv(data_file, index=False)
        
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            validate_data_availability(str(data_file), min_samples=1000)
        
        assert "Data availability error" in str(exc_info.value)
        assert "N = 999" in str(exc_info.value)
        assert "1000" in str(exc_info.value)

    def test_missing_data_file(self, tmp_path):
        """Test that a missing data file raises FileNotFoundError."""
        missing_file = tmp_path / "nonexistent.csv"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_data_availability(str(missing_file), min_samples=1000)
        
        assert "not found" in str(exc_info.value).lower()

    def test_exceeds_minimum_threshold(self, tmp_path):
        """Test that a dataset significantly above threshold passes."""
        # Create a mock dataset with 5000 rows
        mock_data = pd.DataFrame({
            'composition': ['Fe50Co30Ni20'] * 5000,
            'critical_cooling_rate': [100.0] * 5000
        })
        
        data_file = tmp_path / "processed_alloys_raw.csv"
        mock_data.to_csv(data_file, index=False)
        
        result = validate_data_availability(str(data_file), min_samples=1000)
        assert result is True