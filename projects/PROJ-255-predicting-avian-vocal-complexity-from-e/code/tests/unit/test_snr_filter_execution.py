"""
Unit test for T017b: Default Execution of SNR Filtering.

Verifies that the runner script correctly invokes the filtering logic
and produces the expected output files.
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocessing import filter_by_snr_threshold

class TestSNRFilterExecution:
    
    @pytest.fixture
    def sample_data(self, tmp_path):
        """Create a temporary CSV with sample noise_mapped data."""
        data = {
            "record_id": ["rec1", "rec2", "rec3", "rec4", "rec5"],
            "species_id": ["spA", "spA", "spB", "spC", "spD"],
            "location_id": ["loc1", "loc1", "loc2", "loc2", "loc3"],
            "snr_db": [5.0, 12.0, 8.0, 15.0, 20.0],  # Mix of low and high SNR
            "noise_level_db": [60, 40, 30, 50, 60]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "noise_mapped.csv"
        df.to_csv(csv_path, index=False)
        return csv_path

    def test_filter_logic_retains_high_snr(self, sample_data, tmp_path):
        """Test that filter_by_snr_threshold retains records with SNR > 10."""
        output_path = tmp_path / "filtered_snr.csv"
        dropped_path = tmp_path / "dropped_snr.csv"
        
        filtered_df, dropped_df = filter_by_snr_threshold(
            input_path=str(sample_data),
            threshold_db=10.0,
            output_path=str(output_path),
            dropped_log_path=str(dropped_path)
        )

        # Check retained records (SNR > 10)
        assert len(filtered_df) == 3
        assert set(filtered_df["record_id"]) == {"rec2", "rec4", "rec5"}
        
        # Check dropped records (SNR <= 10)
        assert len(dropped_df) == 2
        assert set(dropped_df["record_id"]) == {"rec1", "rec3"}

    def test_filter_logic_creates_files(self, sample_data, tmp_path):
        """Test that output files are physically created on disk."""
        output_path = tmp_path / "filtered_snr.csv"
        dropped_path = tmp_path / "dropped_snr.csv"
        
        filter_by_snr_threshold(
            input_path=str(sample_data),
            threshold_db=10.0,
            output_path=str(output_path),
            dropped_log_path=str(dropped_path)
        )

        assert output_path.exists(), f"Output file {output_path} was not created."
        assert dropped_path.exists(), f"Dropped log {dropped_path} was not created."

    def test_filter_logic_empty_dropped(self, tmp_path):
        """Test behavior when all records pass the threshold."""
        data = {
            "record_id": ["rec1", "rec2"],
            "snr_db": [20.0, 30.0]
        }
        input_csv = tmp_path / "input.csv"
        pd.DataFrame(data).to_csv(input_csv, index=False)
        
        output_path = tmp_path / "out.csv"
        dropped_path = tmp_path / "dropped.csv"
        
        filtered_df, dropped_df = filter_by_snr_threshold(
            input_path=str(input_csv),
            threshold_db=10.0,
            output_path=str(output_path),
            dropped_log_path=str(dropped_path)
        )

        assert len(filtered_df) == 2
        assert len(dropped_df) == 0
        assert dropped_path.exists() # File should still be created, even if empty
        assert dropped_path.stat().st_size > 0 # Should have header at least