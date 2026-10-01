"""
Unit tests for T028d: Derive Time-of-Day.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from derive_time_of_day import categorize_hour, derive_time_of_day

class TestCategorizeHour:
    def test_morning(self):
        assert categorize_hour(6) == "Morning"
        assert categorize_hour(11) == "Morning"
    
    def test_afternoon(self):
        assert categorize_hour(12) == "Afternoon"
        assert categorize_hour(17) == "Afternoon"
    
    def test_evening(self):
        assert categorize_hour(18) == "Evening"
        assert categorize_hour(23) == "Evening"
    
    def test_night(self):
        assert categorize_hour(0) == "Night"
        assert categorize_hour(5) == "Night"
    
    def test_boundary_conditions(self):
        assert categorize_hour(11) == "Morning"
        assert categorize_hour(12) == "Afternoon"
        assert categorize_hour(17) == "Afternoon"
        assert categorize_hour(18) == "Evening"
        assert categorize_hour(23) == "Evening"
        assert categorize_hour(0) == "Night"
        assert categorize_hour(5) == "Night"

class TestDeriveTimeOfDay:
    @pytest.fixture
    def sample_data(self):
        """Create a temporary CSV with sample data."""
        data = {
            'participant_id': ['p1', 'p2', 'p3', 'p4'],
            'timestamp': [
                '2016-01-01 08:30:00',  # Morning
                '2016-01-01 14:15:00',  # Afternoon
                '2016-01-01 19:45:00',  # Evening
                '2016-01-01 02:30:00'   # Night
            ]
        }
        return pd.DataFrame(data)

    def test_derivation(self, sample_data):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            sample_data.to_csv(input_path, index=False)
            
            derive_time_of_day(input_path, output_path)
            
            assert output_path.exists()
            
            result = pd.read_csv(output_path)
            
            assert 'time_of_day' in result.columns
            assert 'hour' in result.columns
            assert len(result) == 4
            
            # Check specific values
            expected_hours = [8, 14, 19, 2]
            expected_cats = ["Morning", "Afternoon", "Evening", "Night"]
            
            assert result['hour'].tolist() == expected_hours
            assert result['time_of_day'].tolist() == expected_cats

    def test_invalid_timestamps(self):
        data = {
            'participant_id': ['p1', 'p2'],
            'timestamp': ['invalid-date', '2016-01-01 08:00:00']
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            df.to_csv(input_path, index=False)
            
            # Should not raise, but drop invalid rows
            count = derive_time_of_day(input_path, output_path)
            
            assert count == 1
            result = pd.read_csv(output_path)
            assert len(result) == 1
            assert result.iloc[0]['time_of_day'] == "Morning"

    def test_missing_timestamp_column(self):
        data = {
            'participant_id': ['p1'],
            'other_col': ['val']
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            df.to_csv(input_path, index=False)
            
            with pytest.raises(ValueError, match="missing required column 'timestamp'"):
                derive_time_of_day(input_path, output_path)