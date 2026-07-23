"""
Unit tests for generate_regression_data.py (T032).

Tests verify that the script correctly loads processed logs,
generates regression data, and saves it to CSV.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.tradeoff_model import generate_regression_data
from analysis.generate_regression_data import save_regression_data_to_csv, main


class TestSaveRegressionDataToCsv:
    """Tests for save_regression_data_to_csv function."""

    def test_save_single_point(self, tmp_path):
        """Test saving a single regression data point."""
        data = [
            {"token_reduction_pct": 50.0, "error_rate": 0.05, "depth": 5}
        ]
        output_path = tmp_path / "test.csv"

        save_regression_data_to_csv(data, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert float(rows[0]['token_reduction_pct']) == 50.0
            assert float(rows[0]['error_rate']) == 0.05
            assert int(rows[0]['depth']) == 5

    def test_save_multiple_points(self, tmp_path):
        """Test saving multiple regression data points."""
        data = [
            {"token_reduction_pct": 10.0, "error_rate": 0.01, "depth": 2},
            {"token_reduction_pct": 20.0, "error_rate": 0.02, "depth": 3},
            {"token_reduction_pct": 90.0, "error_rate": 0.50, "depth": 10}
        ]
        output_path = tmp_path / "test.csv"

        save_regression_data_to_csv(data, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3

    def test_empty_data_raises_error(self, tmp_path):
        """Test that empty data raises ValueError."""
        output_path = tmp_path / "test.csv"

        with pytest.raises(ValueError, match="No regression data to save"):
            save_regression_data_to_csv([], output_path)

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        data = [{"x": 1}]
        output_path = tmp_path / "subdir" / "nested" / "test.csv"

        save_regression_data_to_csv(data, output_path)

        assert output_path.exists()


class TestMain:
    """Tests for the main function."""

    @patch('analysis.generate_regression_data.load_processed_logs')
    @patch('analysis.generate_regression_data.generate_regression_data')
    def test_main_success(self, mock_gen_data, mock_load_logs, tmp_path):
        """Test main function with successful execution."""
        # Setup mocks
        mock_logs = [{"id": 1}, {"id": 2}]
        mock_load_logs.return_value = mock_logs
        mock_regression_data = [
            {"token_reduction_pct": 50.0, "error_rate": 0.05}
        ]
        mock_gen_data.return_value = mock_regression_data

        # Create required directories
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True)

        # Patch paths
        with patch('analysis.generate_regression_data.project_root', tmp_path):
            result = main()

        assert result == 0
        mock_load_logs.assert_called_once()
        mock_gen_data.assert_called_once()

    @patch('analysis.generate_regression_data.load_processed_logs')
    def test_main_no_logs(self, mock_load_logs, tmp_path):
        """Test main function when no logs are found."""
        mock_load_logs.return_value = []

        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        with patch('analysis.generate_regression_data.project_root', tmp_path):
            result = main()

        assert result == 1

    @patch('analysis.generate_regression_data.load_processed_logs')
    @patch('analysis.generate_regression_data.generate_regression_data')
    def test_main_no_regression_data(self, mock_gen_data, mock_load_logs, tmp_path):
        """Test main function when regression data generation fails."""
        mock_load_logs.return_value = [{"id": 1}]
        mock_gen_data.return_value = []

        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        with patch('analysis.generate_regression_data.project_root', tmp_path):
            result = main()

        assert result == 1

    def test_main_missing_processed_dir(self, tmp_path):
        """Test main function when processed logs directory is missing."""
        # Do not create the processed directory
        with patch('analysis.generate_regression_data.project_root', tmp_path):
            result = main()

        assert result == 1