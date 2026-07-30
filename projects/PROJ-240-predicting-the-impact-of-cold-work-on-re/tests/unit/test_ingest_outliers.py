import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from code.ingest import clip_outliers, run_ingestion_pipeline

class TestClipOutliers:
    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame with known outliers."""
        data = {
            "time_to_peak_minutes": [10.0, 12.0, 11.5, 100.0, 150.0, 11.0, 12.5],
            "cold_work_percent": [10, 20, 15, 30, 40, 10, 25],
            "Mn_content": [0.5, 0.6, 0.55, 0.7, 0.8, 0.5, 0.65]
        }
        return pd.DataFrame(data)

    def test_clip_outliers_threshold(self, sample_data):
        """Test that values above 99th percentile are clipped."""
        # The 99th percentile of [10, 12, 11.5, 100, 150, 11, 12.5] is high,
        # but 150 is likely the max. Let's force a lower percentile for testing.
        df, clipped = clip_outliers(sample_data, column="time_to_peak_minutes", percentile=90)
        
        # Calculate expected threshold manually for 90th percentile
        expected_threshold = np.percentile(sample_data["time_to_peak_minutes"], 90)
        
        # Check that no value exceeds the threshold
        assert all(df["time_to_peak_minutes"] <= expected_threshold + 1e-6)
        
        # Check that we captured the outlier
        assert len(clipped) > 0
        assert any(c["original_value"] > expected_threshold for c in clipped)

    def test_clip_outliers_no_outliers(self, sample_data):
        """Test that no clipping occurs if no outliers exist."""
        # Create data where max is within 99th percentile
        data = {
            "time_to_peak_minutes": [10.0, 11.0, 12.0, 13.0, 14.0]
        }
        df_small = pd.DataFrame(data)
        
        df_result, clipped = clip_outliers(df_small, column="time_to_peak_minutes", percentile=99)
        
        assert len(clipped) == 0
        assert df_result.equals(df_small)

    def test_clip_outliers_log_file(self, sample_data):
        """Test that clipping log is written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "clip_log.json")
            
            df, clipped = clip_outliers(
                sample_data, 
                column="time_to_peak_minutes", 
                percentile=90, 
                log_path=log_path
            )
            
            # Check log file exists
            assert os.path.exists(log_path)
            
            # Check log content
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert "column" in log_data
            assert log_data["column"] == "time_to_peak_minutes"
            assert "rows_clipped" in log_data
            assert log_data["rows_clipped"] == len(clipped)
            assert "clipped_details" in log_data
            assert len(log_data["clipped_details"]) == len(clipped)

    def test_clip_outliers_missing_column(self, sample_data):
        """Test that ValueError is raised for missing column."""
        with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
            clip_outliers(sample_data, column="nonexistent")

class TestRunIngestionPipelineOutliers:
    @pytest.fixture
    def temp_csv(self):
        """Create a temporary CSV file with sample data."""
        data = {
            "time_to_peak_minutes": [10.0, 11.0, 12.0, 100.0, 150.0, 11.5, 12.5],
            "cold_work_percent": [10, 20, 15, 30, 40, 10, 25],
            "Mn_content": [0.5, 0.6, 0.55, 0.7, 0.8, 0.5, 0.65],
            "alloy_type": ["A", "A", "A", "B", "B", "A", "B"]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            return f.name

    def test_pipeline_clips_outliers(self, temp_csv):
        """Test that the full pipeline clips outliers and logs them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            log_path = os.path.join(tmpdir, "validation_log.json")
            clip_log_path = os.path.join(tmpdir, "clip_log.json")
            
            summary = run_ingestion_pipeline(
                temp_csv, 
                output_path, 
                log_path, 
                clip_log_path
            )
            
            # Check output exists
            assert os.path.exists(output_path)
            
            # Check summary reports clipping
            assert summary["rows_clipped_outliers"] > 0
            
            # Check clip log exists
            assert os.path.exists(clip_log_path)
            
            # Verify output values are capped
            df_out = pd.read_csv(output_path)
            threshold = np.percentile(pd.read_csv(temp_csv)["time_to_peak_minutes"], 99)
            assert all(df_out["time_to_peak_minutes"] <= threshold + 1e-6)
    
    def test_pipeline_missing_input(self):
        """Test that pipeline fails loudly on missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            log_path = os.path.join(tmpdir, "validation_log.json")
            
            with pytest.raises(FileNotFoundError):
                run_ingestion_pipeline(
                    "nonexistent.csv", 
                    output_path, 
                    log_path
                )