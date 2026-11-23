"""
Unit tests for generate_sensitivity_table.py
"""

import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the code directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.generate_sensitivity_table import (
    load_sensitivity_results,
    format_p_value,
    format_effect_size,
    format_significance,
    generate_table_csv
)


class TestFormatFunctions:
    """Tests for formatting helper functions."""

    def test_format_p_value(self):
        """Test p-value formatting."""
        assert format_p_value(0.05) == "0.0500"
        assert format_p_value(0.00123) == "0.0012"
        assert format_p_value(0.99999) == "1.0000"

    def test_format_effect_size(self):
        """Test effect size formatting."""
        assert format_effect_size(0.12345) == "0.1235"
        assert format_effect_size(-0.5) == "-0.5000"
        assert format_effect_size(0.0) == "0.0000"

    def test_format_significance(self):
        """Test significance formatting."""
        assert format_significance(True) == "Yes"
        assert format_significance(False) == "No"


class TestLoadSensitivityResults:
    """Tests for loading sensitivity results."""

    @patch('analysis.generate_sensitivity_table.get_project_root')
    @patch('analysis.generate_sensitivity_table.get_path')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.load')
    def test_load_results_list_format(self, mock_json_load, mock_open, mock_get_path, mock_get_root):
        """Test loading results when JSON is a list."""
        mock_get_root.return_value = Path("/fake/root")
        mock_get_path.return_value = Path("/fake/root/data/processed/sensitivity_results.json")
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_json_load.return_value = [
            {"threshold_hop": 2, "p_value": 0.03, "effect_size": 0.15, "is_significant": True},
            {"threshold_hop": 3, "p_value": 0.12, "effect_size": 0.08, "is_significant": False}
        ]

        results = load_sensitivity_results()

        assert len(results) == 2
        assert results[0]["threshold_hop"] == 2
        assert results[1]["is_significant"] == False

    @patch('analysis.generate_sensitivity_table.get_project_root')
    @patch('analysis.generate_sensitivity_table.get_path')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.load')
    def test_load_results_dict_format(self, mock_json_load, mock_open, mock_get_path, mock_get_root):
        """Test loading results when JSON is a dict with 'results' key."""
        mock_get_root.return_value = Path("/fake/root")
        mock_get_path.return_value = Path("/fake/root/data/processed/sensitivity_results.json")
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_json_load.return_value = {
            "results": [
                {"threshold_hop": 2, "p_value": 0.03}
            ]
        }

        results = load_sensitivity_results()

        assert len(results) == 1
        assert results[0]["threshold_hop"] == 2

    @patch('analysis.generate_sensitivity_table.get_project_root')
    @patch('analysis.generate_sensitivity_table.get_path')
    def test_load_results_file_not_found(self, mock_get_path, mock_get_root):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        mock_get_root.return_value = Path("/fake/root")
        mock_get_path.return_value = Path("/fake/root/data/processed/sensitivity_results.json")

        with pytest.raises(FileNotFoundError):
            load_sensitivity_results()


class TestGenerateTableCsv:
    """Tests for CSV generation."""

    def test_generate_table_csv_creates_file(self):
        """Test that the CSV file is created with correct columns and data."""
        results = [
            {"threshold_hop": 2, "p_value": 0.03, "effect_size": 0.15, "is_significant": True},
            {"threshold_hop": 3, "p_value": 0.12, "effect_size": 0.08, "is_significant": False},
            {"threshold_hop": 4, "p_value": 0.001, "effect_size": 0.25, "is_significant": True}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sensitivity.csv"

            generate_table_csv(results, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 3
                assert rows[0]['threshold_hop'] == '2'
                assert rows[0]['p_value'] == '0.0300'
                assert rows[0]['effect_size'] == '0.1500'
                assert rows[0]['is_significant'] == 'Yes'

                assert rows[2]['is_significant'] == 'Yes'
                assert rows[1]['is_significant'] == 'No'

    def test_generate_table_csv_empty_results(self):
        """Test CSV generation with empty results list."""
        results = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_empty.csv"

            generate_table_csv(results, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 0
                # Check header exists
                f.seek(0)
                header = f.readline().strip()
                assert header == "threshold_hop,p_value,effect_size,is_significant"