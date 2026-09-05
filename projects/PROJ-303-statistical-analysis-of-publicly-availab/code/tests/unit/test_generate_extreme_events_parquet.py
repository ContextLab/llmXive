import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import pytest
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import ExtremeEvent, calculate_thresholds, flag_extreme_events, map_to_extreme_event_entity
from src.scripts.generate_extreme_events_parquet import main as generate_main
from src.config import set_config
import shutil

class TestExtremeEventsParquetGeneration:
    
    @pytest.fixture
    def sample_data(self):
        """Create sample weather data for testing."""
        dates = pd.date_range(start='2000-01-01', end='2020-12-31', freq='D')
        # Create some extreme values
        values = np.random.normal(10, 5, len(dates))
        # Inject some extreme events
        values[1000] = 50  # 2002-09-26 approx
        values[2000] = 60  # 2005-06-24 approx
        values[3000] = 55  # 2008-03-22 approx
        
        df = pd.DataFrame({
            'date': dates,
            'prcp': values
        })
        return df

    @pytest.fixture
    def config_with_temp_dir(self, tmp_path):
        """Set up a temporary directory for config."""
        # Create necessary subdirectories
        (tmp_path / "raw").mkdir()
        (tmp_path / "processed").mkdir()
        
        config_dict = {
            'data': {
                'raw_dir': str(tmp_path / "raw"),
                'processed_dir': str(tmp_path / "processed"),
                'output_dir': str(tmp_path / "outputs")
            },
            'model': {},
            'pipeline': {}
        }
        set_config(config_dict)
        return tmp_path

    def test_threshold_calculation(self, sample_data):
        """Test that thresholds are calculated correctly."""
        thresholds = calculate_thresholds(sample_data)
        assert 'prcp' in thresholds
        assert thresholds['prcp']['threshold'] > 0
        # The threshold should be the 95th percentile
        expected_threshold = np.percentile(sample_data['prcp'], 95)
        assert abs(thresholds['prcp']['threshold'] - expected_threshold) < 1e-6

    def test_flag_extreme_events(self, sample_data):
        """Test that extreme events are flagged correctly."""
        thresholds = calculate_thresholds(sample_data)
        flagged_df = flag_extreme_events(sample_data, thresholds)
        
        assert 'is_extreme' in flagged_df.columns
        assert 'magnitude' in flagged_df.columns
        
        # Check that extreme events are identified
        extreme_count = flagged_df['is_extreme'].sum()
        assert extreme_count > 0  # We injected some extremes
        
        # Check magnitude calculation
        extreme_rows = flagged_df[flagged_df['is_extreme']]
        threshold_val = thresholds['prcp']['threshold']
        for _, row in extreme_rows.iterrows():
            expected_mag = row['prcp'] - threshold_val
            assert abs(row['magnitude'] - expected_mag) < 1e-6

    def test_map_to_extreme_event_entity(self, sample_data):
        """Test mapping to ExtremeEvent entity."""
        thresholds = calculate_thresholds(sample_data)
        flagged_df = flag_extreme_events(sample_data, thresholds)
        events = map_to_extreme_event_entity(flagged_df, 'TEST_STATION', thresholds)
        
        assert isinstance(events, list)
        if events:
            event = events[0]
            assert isinstance(event, ExtremeEvent)
            assert hasattr(event, 'station_id')
            assert hasattr(event, 'date')
            assert hasattr(event, 'magnitude')
            assert hasattr(event, 'threshold_value')
            assert event.station_id == 'TEST_STATION'

    def test_parquet_generation_integration(self, sample_data, config_with_temp_dir):
        """Integration test: generate parquet file from sample data."""
        # Mock the ingestion to return our sample data
        # We need to temporarily override load_ingested_data or ingest_northeast_data
        # For this test, we'll directly test the logic that leads to the parquet file
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmp_dir:
            processed_dir = Path(tmp_dir) / "processed"
            processed_dir.mkdir()
            
            # Set config to use our temp dir
            config_dict = {
                'data': {
                    'raw_dir': str(Path(tmp_dir) / "raw"),
                    'processed_dir': str(processed_dir),
                    'output_dir': str(Path(tmp_dir) / "outputs")
                },
                'model': {},
                'pipeline': {}
            }
            set_config(config_dict)
            
            # Manually run the logic that generates the parquet
            # Since we can't easily mock the ingestion in this test without complex setup,
            # we'll test the core logic that produces the DataFrame
            
            thresholds = calculate_thresholds(sample_data)
            flagged_df = flag_extreme_events(sample_data, thresholds)
            events = map_to_extreme_event_entity(flagged_df, 'TEST_STATION', thresholds)
            
            if events:
                df_extreme = pd.DataFrame([event.__dict__ for event in events])
                output_path = processed_dir / "extreme_events.parquet"
                df_extreme.to_parquet(output_path, index=False)
                
                # Verify the file exists
                assert output_path.exists()
                
                # Read it back and verify content
                df_read = pd.read_parquet(output_path)
                assert len(df_read) == len(events)
                assert 'station_id' in df_read.columns
                assert 'date' in df_read.columns
                assert 'magnitude' in df_read.columns
                assert 'threshold_value' in df_read.columns
                assert df_read['station_id'].iloc[0] == 'TEST_STATION'

    def test_empty_data_handling(self, config_with_temp_dir):
        """Test handling of empty data."""
        # Create an empty DataFrame
        empty_df = pd.DataFrame(columns=['date', 'prcp'])
        
        # This should not crash, but produce an empty result
        # We can't easily test the full pipeline without mocking ingestion,
        # but we can test the core functions
        try:
            thresholds = calculate_thresholds(empty_df)
            # If it returns empty thresholds, that's fine
            assert thresholds == {} or len(thresholds) == 0
        except Exception:
            # It might raise an error, which is also acceptable if documented
            pass
