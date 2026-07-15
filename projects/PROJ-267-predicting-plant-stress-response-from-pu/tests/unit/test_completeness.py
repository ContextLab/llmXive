"""
Unit tests for T018: code/data_ingestion/completeness.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data_ingestion.completeness import (
    calculate_completeness,
    load_pipeline_summary,
    write_completeness_report,
    run_completeness_check
)
from utils.config import RESULTS_PATH, PIPELINE_SUMMARY_PATH


class TestCalculateCompleteness:
    """Tests for the calculate_completeness function."""

    def test_standard_case(self):
        """Test normal calculation."""
        result = calculate_completeness(100, 80)
        assert result == 80.0

    def test_perfect_completeness(self):
        """Test 100% retention."""
        result = calculate_completeness(50, 50)
        assert result == 100.0

    def test_zero_retention(self):
        """Test 0% retention."""
        result = calculate_completeness(100, 0)
        assert result == 0.0

    def test_zero_initial_count(self):
        """Test handling of division by zero (0 initial)."""
        result = calculate_completeness(0, 0)
        assert result == 0.0

    def test_float_precision(self):
        """Test precision handling."""
        # 1/3 = 33.3333...
        result = calculate_completeness(3, 1)
        assert result == 33.3333


class TestLoadPipelineSummary:
    """Tests for load_pipeline_summary."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {
            "initial_query_count": 10,
            "retained_dataset_count": 5,
            "other_field": "ignored"
        }
        test_file = tmp_path / "summary.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        with patch('data_ingestion.completeness.PIPELINE_SUMMARY_PATH', test_file):
            result = load_pipeline_summary()

        assert result == test_data

    def test_missing_file_raises(self, tmp_path):
        """Test that FileNotFoundError is raised if file missing."""
        non_existent = tmp_path / "missing.json"
        with patch('data_ingestion.completeness.PIPELINE_SUMMARY_PATH', non_existent):
            with pytest.raises(FileNotFoundError):
                load_pipeline_summary()

    def test_missing_keys_raises(self, tmp_path):
        """Test that KeyError is raised if required keys missing."""
        test_data = {"initial_query_count": 10} # Missing retained
        test_file = tmp_path / "bad_summary.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        with patch('data_ingestion.completeness.PIPELINE_SUMMARY_PATH', test_file):
            with pytest.raises(KeyError):
                load_pipeline_summary()


class TestWriteCompletenessReport:
    """Tests for write_completeness_report."""

    def test_writes_correct_json(self, tmp_path):
        """Test that the report is written correctly."""
        metrics = {
            "initial_query_count": 10,
            "retained_dataset_count": 8,
            "completeness_percentage": 80.0,
            "timestamp": "2023-01-01T00:00:00Z"
        }
        output_file = tmp_path / "completeness.json"

        write_completeness_report(metrics, output_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            written = json.load(f)

        assert written == metrics

class TestRunCompletenessCheck:
    """Integration-style tests for the main runner."""

    @patch('data_ingestion.completeness.PIPELINE_SUMMARY_PATH')
    @patch('data_ingestion.completeness.RESULTS_PATH')
    def test_full_run_success(self, mock_results_path, mock_summary_path, tmp_path):
        """Test a successful run end-to-end with mocked paths."""
        # Setup mock paths
        mock_summary_path.__truediv__ = lambda self, key: tmp_path / "summary.json"
        mock_summary_path.__fspath__ = lambda self: str(tmp_path / "summary.json")
        mock_results_path.__truediv__ = lambda self, key: tmp_path / "output.json"
        mock_results_path.__fspath__ = lambda self: str(tmp_path)
        mock_results_path.mkdir = lambda *args, **kwargs: None

        # Create input file
        input_data = {
            "initial_query_count": 20,
            "retained_dataset_count": 18
        }
        input_file = tmp_path / "summary.json"
        with open(input_file, 'w') as f:
            json.dump(input_data, f)

        # Mock the path object to return our temp file
        with patch('data_ingestion.completeness.PIPELINE_SUMMARY_PATH', input_file):
            with patch('data_ingestion.completeness.RESULTS_PATH', tmp_path):
                result = run_completeness_check()

        assert result['completeness_percentage'] == 90.0
        assert (tmp_path / "data_completeness.json").exists()