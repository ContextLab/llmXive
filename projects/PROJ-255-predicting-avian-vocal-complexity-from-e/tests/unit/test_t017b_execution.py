import os
import sys
import tempfile
import pytest
import csv
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import filter_by_snr_threshold, load_csv

class TestT017bExecution:
    """Tests for T017b: Default Execution of SNR Filtering."""

    def test_filtering_produces_expected_output_files(self, tmp_path):
        """
        Verify that running the filter with default threshold produces
        both the filtered CSV and the dropped records CSV.
        """
        # Setup input data
        input_file = tmp_path / "noise_mapped.csv"
        output_file = tmp_path / "filtered_snr.csv"
        dropped_file = tmp_path / "dropped_snr.csv"

        # Create a mock input dataset with mixed SNR values
        # Required columns based on T015 output schema
        mock_data = [
            {"record_id": "1", "species_id": "sp_A", "snr_db": 15.0, "noise_level_db": 60},
            {"record_id": "2", "species_id": "sp_B", "snr_db": 5.0, "noise_level_db": 70}, # Should be dropped
            {"record_id": "3", "species_id": "sp_A", "snr_db": 12.0, "noise_level_db": 50},
            {"record_id": "4", "species_id": "sp_C", "snr_db": 8.0, "noise_level_db": 65}, # Should be dropped
            {"record_id": "5", "species_id": "sp_B", "snr_db": 10.0, "noise_level_db": 55}, # Boundary (>= 10)
        ]

        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=mock_data[0].keys())
            writer.writeheader()
            writer.writerows(mock_data)

        # Execute filter with default threshold (10.0)
        filter_by_snr_threshold(
            input_path=str(input_file),
            threshold_db=10.0,
            output_path=str(output_file),
            dropped_path=str(dropped_file)
        )

        # Assert output files exist
        assert output_file.exists(), "Filtered output file was not created"
        assert dropped_file.exists(), "Dropped records file was not created"

        # Verify content of filtered file
        filtered_data = load_csv(str(output_file))
        assert len(filtered_data) == 3, f"Expected 3 retained records, got {len(filtered_data)}"
        
        retained_ids = {r['record_id'] for r in filtered_data}
        assert "1" in retained_ids
        assert "3" in retained_ids
        assert "5" in retained_ids # 10.0 >= 10.0 should be kept

        # Verify content of dropped file
        dropped_data = load_csv(str(dropped_file))
        assert len(dropped_data) == 2, f"Expected 2 dropped records, got {len(dropped_data)}"
        
        dropped_ids = {r['record_id'] for r in dropped_data}
        assert "2" in dropped_ids
        assert "4" in dropped_ids

    def test_filtering_handles_empty_input(self, tmp_path):
        """Verify behavior when input file is empty (header only)."""
        input_file = tmp_path / "noise_mapped.csv"
        output_file = tmp_path / "filtered_snr.csv"
        dropped_file = tmp_path / "dropped_snr.csv"

        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["record_id", "species_id", "snr_db", "noise_level_db"])
            writer.writeheader()

        filter_by_snr_threshold(
            input_path=str(input_file),
            threshold_db=10.0,
            output_path=str(output_file),
            dropped_path=str(dropped_file)
        )

        assert output_file.exists()
        assert dropped_file.exists()
        
        # Both should be empty (header only)
        assert len(load_csv(str(output_file))) == 0
        assert len(load_csv(str(dropped_file))) == 0
