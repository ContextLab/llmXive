import pytest
import pandas as pd
from preprocess import deduplicate_events

class TestDeduplication:
    def test_deduplication_retains_most_recent_revision(self):
        """
        Test that deduplication keeps the record with the latest timestamp for the same ID.
        """
        # Create a dataframe with duplicate IDs but different timestamps
        data = {
            'id': ['eq_001', 'eq_001', 'eq_002', 'eq_003', 'eq_003'],
            'timestamp': [
                '2023-01-01 10:00:00', # Old revision of eq_001
                '2023-01-01 12:00:00', # New revision of eq_001
                '2023-01-02 08:00:00', # eq_002
                '2023-01-03 09:00:00', # Old revision of eq_003
                '2023-01-03 11:00:00'  # New revision of eq_003
            ],
            'magnitude': [4.5, 4.6, 5.0, 3.0, 3.1],
            'lat': [1.0, 1.0, 2.0, 3.0, 3.0],
            'lon': [1.0, 1.0, 2.0, 3.0, 3.0]
        }
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Run deduplication
        result = deduplicate_events(df)

        # Verify row count
        assert len(result) == 3, "Should have 3 unique events"

        # Verify specific IDs have the correct timestamp (most recent)
        eq_001_row = result[result['id'] == 'eq_001'].iloc[0]
        assert eq_001_row['timestamp'] == pd.Timestamp('2023-01-01 12:00:00'), "eq_001 should be the newer revision"
        assert eq_001_row['magnitude'] == 4.6, "eq_001 magnitude should be from newer revision"

        eq_003_row = result[result['id'] == 'eq_003'].iloc[0]
        assert eq_003_row['timestamp'] == pd.Timestamp('2023-01-03 11:00:00'), "eq_003 should be the newer revision"
        assert eq_003_row['magnitude'] == 3.1, "eq_003 magnitude should be from newer revision"

    def test_deduplication_empty_dataframe(self):
        """Test that an empty dataframe returns an empty dataframe."""
        df = pd.DataFrame(columns=['id', 'timestamp', 'magnitude'])
        result = deduplicate_events(df)
        assert len(result) == 0

    def test_deduplication_no_duplicates(self):
        """Test that a dataframe with no duplicates is returned unchanged (except for sort order)."""
        data = {
            'id': ['eq_001', 'eq_002'],
            'timestamp': ['2023-01-01', '2023-01-02'],
            'magnitude': [4.0, 5.0],
            'lat': [1.0, 2.0],
            'lon': [1.0, 2.0]
        }
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        result = deduplicate_events(df)
        
        assert len(result) == 2
        assert set(result['id']) == {'eq_001', 'eq_002'}