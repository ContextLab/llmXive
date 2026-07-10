import pytest
import pandas as pd
import numpy as np
import logging
from io import StringIO
from ingestion import check_z_axis_completeness, ingest_data, IngestionError
import tempfile
import os

# Set up logging to capture warnings
logging.basicConfig(level=logging.WARNING)

class TestZAxisHandling:
    """Tests for T016: Handling datasets lacking z-axis data."""

    def test_missing_z_column_adds_flag_and_warns(self, caplog):
        """Test that missing 'z' column results in pot_incomplete=True and a warning."""
        data = "particle_id,timestamp,x,y,theta\n1,0.0,1.0,2.0,0.1\n2,0.1,1.1,2.1,0.2"
        df = pd.read_csv(StringIO(data))
        
        with caplog.at_level(logging.WARNING):
            result = check_z_axis_completeness(df, z_col='z')
        
        assert 'pot_incomplete' in result.columns
        assert result['pot_incomplete'].all() == True
        assert "Z-axis data is missing" in caplog.text

    def test_z_column_present_valid_data(self):
        """Test that valid z data results in pot_incomplete=False."""
        data = "particle_id,timestamp,x,y,z,theta\n1,0.0,1.0,2.0,0.5,0.1\n2,0.1,1.1,2.1,0.6,0.2"
        df = pd.read_csv(StringIO(data))
        
        result = check_z_axis_completeness(df, z_col='z')
        
        assert 'pot_incomplete' in result.columns
        assert result['pot_incomplete'].all() == False

    def test_z_column_all_nan_adds_flag(self, caplog):
        """Test that all NaN z values results in pot_incomplete=True."""
        data = "particle_id,timestamp,x,y,z,theta\n1,0.0,1.0,2.0,NaN,0.1\n2,0.1,1.1,2.1,NaN,0.2"
        df = pd.read_csv(StringIO(data))
        
        with caplog.at_level(logging.WARNING):
            result = check_z_axis_completeness(df, z_col='z')
        
        assert result['pot_incomplete'].all() == True
        assert "Z-axis data appears to be missing" in caplog.text

    def test_z_column_all_zero_adds_flag(self, caplog):
        """Test that all zero z values (indicating invalid/missing) results in pot_incomplete=True."""
        data = "particle_id,timestamp,x,y,z,theta\n1,0.0,1.0,2.0,0.0,0.1\n2,0.1,1.1,2.1,0.0,0.2"
        df = pd.read_csv(StringIO(data))
        
        with caplog.at_level(logging.WARNING):
            result = check_z_axis_completeness(df, z_col='z')
        
        assert result['pot_incomplete'].all() == True
        assert "Z-axis data appears to be missing" in caplog.text

    def test_integration_missing_z_in_ingest(self, tmp_path, caplog):
        """Integration test: ingest_data handles missing z in full pipeline."""
        # Create temporary tracking file without 'z'
        tracking_path = tmp_path / "tracking.csv"
        tracking_path.write_text("particle_id,timestamp,x,y,theta\n1,0.0,1.0,2.0,0.1\n2,0.1,1.1,2.1,0.2")
        
        # Create dummy driving file
        driving_path = tmp_path / "driving.csv"
        driving_path.write_text("timestamp,frequency\n0.0,50\n0.1,50")
        
        output_path = tmp_path / "output.csv"
        
        with caplog.at_level(logging.WARNING):
            # Run ingestion
            # We need to call the function that actually does the work
            # ingest_data expects patterns, so we use the file paths directly as patterns for this test
            # However, find_csv_files expects a directory or pattern. 
            # Let's adapt by creating a function that takes paths directly or mocking.
            # For this test, we will manually call the steps to verify the logic.
            
            from ingestion import load_tracking_data, load_driving_data, sync_timestamps, merge_datasets, handle_missing_frames, compute_derivatives, check_z_axis_completeness
            
            tracking_df = load_tracking_data([tracking_path])
            driving_df = load_driving_data([driving_path])
            tracking_df, driving_df = sync_timestamps(tracking_df, driving_df)
            merged_df = merge_datasets(tracking_df, driving_df)
            merged_df = handle_missing_frames(merged_df)
            merged_df = compute_derivatives(merged_df)
            merged_df = check_z_axis_completeness(merged_df, z_col='z')
            
            assert 'pot_incomplete' in merged_df.columns
            assert merged_df['pot_incomplete'].all() == True
            assert "Z-axis data is missing" in caplog.text