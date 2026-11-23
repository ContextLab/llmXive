import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import pytest
import sys
import os

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.preprocessing import (
    map_to_extreme_event_entity,
    flag_extreme_events,
    calculate_thresholds,
    ExtremeEvent
)

class TestExtremeEventMapping:
    """
    Unit tests for the ExtremeEvent entity mapping logic (Task T014b).
    Verifies that raw data is correctly mapped to the schema:
    (station_id, date, magnitude, threshold_value)
    """

    def test_mapping_basic_functionality(self):
        """Test that basic mapping creates correct ExtremeEvent objects."""
        # Create sample data
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        threshold = 55.0
        
        # Flag extremes
        df_flagged = flag_extreme_events(df, threshold)
        
        # Map to entities
        events = map_to_extreme_event_entity(df_flagged, station_id="STN_001", threshold_value=threshold)
        
        # Assertions
        assert len(events) == 5  # Values 60, 70, 80, 90, 100 are > 55
        
        # Check the first event
        first_event = events[0]
        assert isinstance(first_event, ExtremeEvent)
        assert first_event.station_id == "STN_001"
        assert first_event.date == "2020-01-07"  # Date of value 60
        assert first_event.magnitude == 60.0
        assert first_event.threshold_value == 55.0

    def test_mapping_no_extremes(self):
        """Test that mapping returns empty list when no extremes exist."""
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        threshold = 100.0  # Higher than any value
        
        df_flagged = flag_extreme_events(df, threshold)
        events = map_to_extreme_event_entity(df_flagged, station_id="STN_002", threshold_value=threshold)
        
        assert len(events) == 0

    def test_mapping_with_missing_values(self):
        """Test that mapping handles missing values correctly."""
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        values = [10.0, np.nan, 30.0, 40.0, 50.0]
        
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        threshold = 25.0
        
        df_flagged = flag_extreme_events(df, threshold)
        events = map_to_extreme_event_entity(df_flagged, station_id="STN_003", threshold_value=threshold)
        
        # Only 30, 40, 50 should be flagged (NaN is not > 25)
        assert len(events) == 3
        assert events[0].magnitude == 30.0
        assert events[1].magnitude == 40.0
        assert events[2].magnitude == 50.0

    def test_mapping_missing_is_extreme_column(self):
        """Test that mapping raises error if 'is_extreme' column is missing."""
        df = pd.DataFrame({
            'date': ['2020-01-01'],
            'value': [50.0]
        })
        
        with pytest.raises(ValueError, match="DataFrame must contain 'is_extreme' column"):
            map_to_extreme_event_entity(df, station_id="STN_004", threshold_value=10.0)

    def test_schema_fields_presence(self):
        """Verify that all required schema fields are present in the output."""
        dates = pd.date_range('2020-01-01', periods=3, freq='D')
        values = [100.0, 101.0, 102.0]
        
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        threshold = 50.0
        df_flagged = flag_extreme_events(df, threshold)
        events = map_to_extreme_event_entity(df_flagged, station_id="STN_005", threshold_value=threshold)
        
        # Check dataclass fields
        required_fields = {'station_id', 'date', 'magnitude', 'threshold_value'}
        event_dict = asdict(events[0])
        
        assert required_fields.issubset(set(event_dict.keys()))
        assert event_dict['station_id'] == "STN_005"
        assert event_dict['threshold_value'] == 50.0
        assert event_dict['magnitude'] == 100.0
        assert event_dict['date'] == "2020-01-01"

def asdict(obj):
    """Helper to convert dataclass to dict if dataclasses not imported in test scope."""
    import dataclasses
    return dataclasses.asdict(obj)
