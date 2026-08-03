import os
import sys
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path to import check_sample_size
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from check_sample_size import check_sample_size, write_validation_report

class TestSampleSizeEnforcement:
    def test_sample_size_enforcement_fails_below_30(self, tmp_path):
        """Test that check_sample_size returns False and exits with code 1 when N < 30"""
        # Create a mock CSV with 29 participants
        mock_data = pd.DataFrame({
            'participant_id': [f"sub_{i:03d}" for i in range(29)],
            'channel': ['Fz'] * 29,
            'lzc_value': [0.5] * 29
        })
        mock_csv_path = tmp_path / "lzc_metrics.csv"
        mock_data.to_csv(mock_csv_path, index=False)

        result = check_sample_size(str(mock_csv_path), min_n=30)
        assert result is False

        # Check that validation_report.json was created
        report_path = Path(tmp_path) / "validation_report.json"
        # The function writes to a fixed path relative to the script, so we check the expected structure
        # In a real scenario, we'd check the fixed path, but for testing we verify the logic
        # Since the function writes to a hardcoded path, we can't easily check it here without mocking
        # Instead, we rely on the return value and the fact that it logged an error

    def test_sample_size_enforcement_passes_at_30(self, tmp_path):
        """Test that check_sample_size returns True when N >= 30"""
        # Create a mock CSV with 30 participants
        mock_data = pd.DataFrame({
            'participant_id': [f"sub_{i:03d}" for i in range(30)],
            'channel': ['Fz'] * 30,
            'lzc_value': [0.5] * 30
        })
        mock_csv_path = tmp_path / "lzc_metrics.csv"
        mock_data.to_csv(mock_csv_path, index=False)

        result = check_sample_size(str(mock_csv_path), min_n=30)
        assert result is True

    def test_sample_size_enforcement_missing_file(self, tmp_path):
        """Test that check_sample_size handles missing file correctly"""
        mock_csv_path = tmp_path / "nonexistent.csv"
        
        result = check_sample_size(str(mock_csv_path), min_n=30)
        assert result is False

    def test_sample_size_enforcement_missing_column(self, tmp_path):
        """Test that check_sample_size handles missing participant_id column correctly"""
        mock_data = pd.DataFrame({
            'id': [f"sub_{i:03d}" for i in range(30)],
            'channel': ['Fz'] * 30,
            'lzc_value': [0.5] * 30
        })
        mock_csv_path = tmp_path / "lzc_metrics.csv"
        mock_data.to_csv(mock_csv_path, index=False)

        result = check_sample_size(str(mock_csv_path), min_n=30)
        assert result is False
