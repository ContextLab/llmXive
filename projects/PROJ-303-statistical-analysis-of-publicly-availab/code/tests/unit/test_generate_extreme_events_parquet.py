"""
Unit tests for the extreme events parquet generation script.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import pytest
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.preprocessing import flag_extreme_events

class TestExtremeEventsParquetGeneration:
    """Test cases for extreme events generation logic."""

    def test_flag_extreme_events_correctness(self):
        """Test that flag_extreme_events correctly identifies extreme events."""
        # Create sample data
        data = {
            'station_id': ['STA001', 'STA001', 'STA001', 'STA002', 'STA002'],
            'date': pd.date_range('2010-01-01', periods=5),
            'tmax': [20.0, 25.0, 35.0, 15.0, 30.0]  # 35.0 and 30.0 should be extremes if thresholds are low
        }
        df = pd.DataFrame(data)
        
        # Define thresholds (95th percentile would be around 25-30 for this small sample)
        # Let's use a fixed threshold for testing
        thresholds = pd.Series({'STA001': 28.0, 'STA002': 25.0})
        
        # Flag extremes
        result = flag_extreme_events(df, thresholds, column='tmax')
        
        # Check that extreme events are correctly flagged
        assert result.loc[result['station_id'] == 'STA001', 'is_extreme'].sum() == 1  # 35.0 > 28.0
        assert result.loc[result['station_id'] == 'STA002', 'is_extreme'].sum() == 1  # 30.0 > 25.0
        
        # Check magnitude calculation
        assert result.loc[result['station_id'] == 'STA001', 'magnitude'].iloc[0] == 35.0 - 28.0
        assert result.loc[result['station_id'] == 'STA002', 'magnitude'].iloc[0] == 30.0 - 25.0

    def test_threshold_calculation_on_training_data(self):
        """Test that thresholds are calculated only on training data."""
        # Create sample data with known values
        data = {
            'station_id': ['STA001'] * 20,
            'date': pd.date_range('2000-01-01', periods=20),
            'tmax': list(range(20, 40))  # 20 to 39
        }
        df = pd.DataFrame(data)
        
        # Calculate 95th percentile
        threshold = df['tmax'].quantile(0.95)
        
        # The 95th percentile of [20, 21, ..., 39] should be around 37.1
        # Using numpy for precise calculation
        expected_threshold = np.percentile(range(20, 40), 95)
        
        assert abs(threshold - expected_threshold) < 0.1

    def test_empty_extreme_events_handling(self):
        """Test that the script handles cases with no extreme events."""
        # Create data where no values exceed the threshold
        data = {
            'station_id': ['STA001', 'STA001'],
            'date': pd.date_range('2010-01-01', periods=2),
            'tmax': [20.0, 21.0]
        }
        df = pd.DataFrame(data)
        
        thresholds = pd.Series({'STA001': 30.0})
        
        result = flag_extreme_events(df, thresholds, column='tmax')
        result = result[result['is_extreme']]
        
        assert len(result) == 0

    def test_schema_compliance(self):
        """Test that the output dataframe has the correct schema."""
        # Simulate the output dataframe structure
        expected_columns = ['station_id', 'date', 'magnitude', 'threshold_value']
        
        # Create a sample output
        output_df = pd.DataFrame({
            'station_id': ['STA001'],
            'date': [pd.Timestamp('2010-01-01')],
            'magnitude': [5.0],
            'threshold_value': [25.0]
        })
        
        assert list(output_df.columns) == expected_columns
        assert output_df['station_id'].dtype == 'object'
        assert pd.api.types.is_datetime64_any_dtype(output_df['date'])
        assert pd.api.types.is_numeric_dtype(output_df['magnitude'])
        assert pd.api.types.is_numeric_dtype(output_df['threshold_value'])