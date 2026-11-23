import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import deduplicate_events

class TestDeduplication:
    """Test cases for T016: Deduplication logic."""

    def setup_method(self):
        """Setup test data."""
        # Create test data with duplicate event IDs but different timestamps
        self.test_data = pd.DataFrame({
            'event_id': ['us12345', 'us12345', 'us67890', 'us67890', 'us11111'],
            'timestamp': pd.to_datetime([
                '2018-01-01 10:00:00',
                '2018-01-01 12:00:00',  # Later revision of us12345
                '2018-02-01 08:00:00',
                '2018-02-01 09:00:00',  # Later revision of us67890
                '2018-03-01 14:00:00'   # Unique event
            ]),
            'magnitude': [4.5, 4.6, 5.0, 5.1, 4.2],
            'pressure_value': [1013.2, 1013.5, 1012.8, 1013.0, 1014.1],
            'anomaly_value': [0.1, 0.4, -0.2, 0.0, 0.5]
        })

    def test_deduplication_keeps_most_recent(self):
        """Test that deduplication retains the most recent revision."""
        result = deduplicate_events(self.test_data)
        
        # Should have 3 unique events
        assert len(result) == 3
        
        # Check that us12345 has the later timestamp (12:00)
        us12345 = result[result['event_id'] == 'us12345']
        assert len(us12345) == 1
        assert us12345['timestamp'].iloc[0] == pd.Timestamp('2018-01-01 12:00:00')
        assert us12345['magnitude'].iloc[0] == 4.6  # Updated magnitude
        
        # Check that us67890 has the later timestamp (09:00)
        us67890 = result[result['event_id'] == 'us67890']
        assert len(us67890) == 1
        assert us67890['timestamp'].iloc[0] == pd.Timestamp('2018-02-01 09:00:00')
        assert us67890['magnitude'].iloc[0] == 5.1  # Updated magnitude
        
        # Check that unique event is preserved
        us11111 = result[result['event_id'] == 'us11111']
        assert len(us11111) == 1
        assert us11111['magnitude'].iloc[0] == 4.2

    def test_deduplication_preserves_data_integrity(self):
        """Test that deduplication preserves all columns for retained rows."""
        result = deduplicate_events(self.test_data)
        
        # Check that all expected columns are present
        expected_cols = ['event_id', 'timestamp', 'magnitude', 'pressure_value', 'anomaly_value']
        for col in expected_cols:
            assert col in result.columns

    def test_deduplication_no_duplicates(self):
        """Test that result contains no duplicate event IDs."""
        result = deduplicate_events(self.test_data)
        
        # Check for duplicates
        duplicates = result[result.duplicated(subset=['event_id'], keep=False)]
        assert len(duplicates) == 0

    def test_deduplication_missing_event_id(self):
        """Test that deduplication raises error if event_id column is missing."""
        df_no_id = self.test_data.drop(columns=['event_id'])
        
        with pytest.raises(ValueError, match="DataFrame must contain 'event_id' column"):
            deduplicate_events(df_no_id)

    def test_deduplication_missing_timestamp(self):
        """Test deduplication behavior when timestamp is missing."""
        df_no_ts = self.test_data.drop(columns=['timestamp'])
        
        # Should not raise, but keep first occurrence
        result = deduplicate_events(df_no_ts)
        
        # Should still have unique event IDs
        assert len(result) == 3
        assert len(result['event_id'].unique()) == 3