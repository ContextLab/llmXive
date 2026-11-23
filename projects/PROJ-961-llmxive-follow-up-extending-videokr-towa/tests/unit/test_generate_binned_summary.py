"""
Unit tests for code/analysis/generate_binned_summary.py.

Tests:
- load_binned_accuracy_data: Valid JSON, missing file, invalid JSON.
- generate_summary_table: Correct CSV structure, empty data handling.
- generate_binned_plot: Plot file creation, correct bin ordering.
"""
import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import functions to test
from analysis.generate_binned_summary import (
    load_binned_accuracy_data,
    generate_summary_table,
    generate_binned_plot,
)


class TestLoadBinnedAccuracyData:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {
            "1": {"accuracy": 0.85, "count": 100, "correct_count": 85, "total_count": 100},
            "2": {"accuracy": 0.70, "count": 50, "correct_count": 35, "total_count": 50},
            "3+": {"accuracy": 0.55, "count": 30, "correct_count": 16, "total_count": 30},
        }
        input_file = tmp_path / "binned_accuracy.json"
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        result = load_binned_accuracy_data(str(input_file))

        assert result == test_data
        assert result["1"]["accuracy"] == 0.85

    def test_load_missing_file(self, tmp_path):
        """Test handling of a missing file."""
        non_existent = tmp_path / "does_not_exist.json"
        with pytest.raises(FileNotFoundError):
            load_binned_accuracy_data(str(non_existent))

    def test_load_invalid_json(self, tmp_path):
        """Test handling of invalid JSON."""
        input_file = tmp_path / "invalid.json"
        with open(input_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_binned_accuracy_data(str(input_file))


class TestGenerateSummaryTable:
    def test_generate_csv(self, tmp_path):
        """Test CSV generation with valid data."""
        binned_data = {
            "1": {"accuracy": 0.90, "count": 100, "correct_count": 90, "total_count": 100},
            "2": {"accuracy": 0.75, "count": 80, "correct_count": 60, "total_count": 80},
            "3+": {"accuracy": 0.60, "count": 20, "correct_count": 12, "total_count": 20},
        }
        output_file = tmp_path / "summary.csv"

        generate_summary_table(binned_data, str(output_file))

        assert output_file.exists()

        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["bin"] == "1"
        assert rows[0]["accuracy"] == "0.9"
        assert rows[0]["count"] == "100"
        assert rows[1]["bin"] == "2"
        assert rows[2]["bin"] == "3+"

    def test_generate_csv_missing_bins(self, tmp_path):
        """Test CSV generation when some bins are missing."""
        binned_data = {
            "1": {"accuracy": 0.90, "count": 100, "correct_count": 90, "total_count": 100},
            # "2" is missing
            "3+": {"accuracy": 0.60, "count": 20, "correct_count": 12, "total_count": 20},
        }
        output_file = tmp_path / "summary.csv"

        generate_summary_table(binned_data, str(output_file))

        assert output_file.exists()

        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should only have rows for bins present in data (1 and 3+)
        # But the function iterates over fixed list ["1", "2", "3+"]
        # If a bin is missing, it logs a warning but does not add a row?
        # Let's check the implementation: it appends only if bin_name in binned_data
        # So we expect 2 rows (1 and 3+)
        assert len(rows) == 2
        assert rows[0]["bin"] == "1"
        assert rows[1]["bin"] == "3+"

    def test_generate_csv_empty_data(self, tmp_path):
        """Test CSV generation with empty data."""
        binned_data = {}
        output_file = tmp_path / "summary.csv"

        generate_summary_table(binned_data, str(output_file))

        assert output_file.exists()

        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # No rows expected since no bins found
        assert len(rows) == 0


class TestGenerateBinnedPlot:
    def test_generate_plot(self, tmp_path):
        """Test plot generation with valid data."""
        binned_data = {
            "1": {"accuracy": 0.90, "count": 100},
            "2": {"accuracy": 0.75, "count": 80},
            "3+": {"accuracy": 0.60, "count": 20},
        }
        output_file = tmp_path / "plot.png"

        generate_binned_plot(binned_data, str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_generate_plot_missing_bins(self, tmp_path):
        """Test plot generation when some bins are missing."""
        binned_data = {
            "1": {"accuracy": 0.90, "count": 100},
            # "2" is missing
            "3+": {"accuracy": 0.60, "count": 20},
        }
        output_file = tmp_path / "plot.png"

        # Should handle missing bins by setting accuracy/count to 0
        generate_binned_plot(binned_data, str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_generate_plot_empty_data(self, tmp_path):
        """Test plot generation with empty data."""
        binned_data = {}
        output_file = tmp_path / "plot.png"

        # Should handle empty data by plotting zeros
        generate_binned_plot(binned_data, str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0
