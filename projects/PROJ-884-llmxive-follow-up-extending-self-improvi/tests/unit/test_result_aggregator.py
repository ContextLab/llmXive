"""
Unit tests for the result aggregator module.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from bes.result_aggregator import (
    load_json_file,
    find_run_logs,
    parse_n_from_filename,
    aggregate_results,
    save_results,
    AggregatedResult,
    AggregatedRunStats
)


class TestLoadJsonFile:
    """Tests for the load_json_file function."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(test_data))

        result = load_json_file(str(test_file))
        assert result == test_data

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file returns None."""
        result = load_json_file(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON returns None."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")

        result = load_json_file(str(test_file))
        assert result is None


class TestFindRunLogs:
    """Tests for the find_run_logs function."""

    def test_find_matching_files(self, tmp_path):
        """Test finding files matching a pattern."""
        # Create test files
        (tmp_path / "bes_N10_symbolic.json").write_text("{}")
        (tmp_path / "bes_N100_symbolic.json").write_text("{}")
        (tmp_path / "bes_N500_symbolic.json").write_text("{}")
        (tmp_path / "other_file.json").write_text("{}")

        pattern = str(tmp_path / "bes_N*_symbolic.json")
        files = find_run_logs(pattern)

        assert len(files) == 3
        assert all("bes_N" in f and "symbolic" in f for f in files)

    def test_find_no_matching_files(self, tmp_path):
        """Test finding files when none match."""
        pattern = str(tmp_path / "nonexistent_*.json")
        files = find_run_logs(pattern)
        assert len(files) == 0


class TestParseNFromFilename:
    """Tests for the parse_n_from_filename function."""

    def test_parse_uppercase_N(self):
        """Test parsing N value from uppercase filename."""
        assert parse_n_from_filename("bes_N10_symbolic.json") == 10
        assert parse_n_from_filename("bes_N100_symbolic.json") == 100

    def test_parse_lowercase_n(self):
        """Test parsing N value from lowercase filename."""
        assert parse_n_from_filename("bes_n10_symbolic.json") == 10
        assert parse_n_from_filename("bes_n500_symbolic.json") == 500

    def test_parse_results_pattern(self):
        """Test parsing from results filename pattern."""
        assert parse_n_from_filename("bes_results_N10.json") == 10
        assert parse_n_from_filename("bes_results_N500.json") == 500

    def test_parse_invalid_filename(self):
        """Test parsing returns None for invalid filename."""
        assert parse_n_from_filename("invalid_filename.json") is None
        assert parse_n_from_filename("bes_abc_symbolic.json") is None


class TestAggregateResults:
    """Tests for the aggregate_results function."""

    @pytest.fixture
    def sample_log_files(self, tmp_path):
        """Create sample log files for testing."""
        log_files = []

        # Create log for N=10
        data_n10 = {
            "n_value": 10,
            "method": "symbolic",
            "population_size": 50,
            "generations": 20,
            "run_id": "run_001",
            "timestamp": "2024-01-01T00:00:00",
            "instances": [
                {"success": True, "elapsed_time": 1.0, "energy_joules": 10.0},
                {"success": True, "elapsed_time": 1.2, "energy_joules": 12.0},
                {"success": False, "elapsed_time": 0.8, "energy_joules": 8.0}
            ]
        }
        file_n10 = tmp_path / "bes_N10_symbolic.json"
        file_n10.write_text(json.dumps(data_n10))
        log_files.append(str(file_n10))

        # Create log for N=100
        data_n100 = {
            "n_value": 100,
            "method": "symbolic",
            "population_size": 50,
            "generations": 20,
            "run_id": "run_002",
            "timestamp": "2024-01-01T01:00:00",
            "instances": [
                {"success": True, "elapsed_time": 5.0, "energy_joules": 50.0},
                {"success": False, "elapsed_time": 4.5, "energy_joules": 45.0}
            ]
        }
        file_n100 = tmp_path / "bes_N100_symbolic.json"
        file_n100.write_text(json.dumps(data_n100))
        log_files.append(str(file_n100))

        return log_files

    def test_aggregate_multiple_files(self, sample_log_files):
        """Test aggregating multiple log files."""
        result = aggregate_results(sample_log_files)

        assert len(result.runs) == 2
        assert result.method == "symbolic"
        assert result.summary["total_runs"] == 2
        assert result.summary["total_instances"] == 5
        assert result.summary["total_successful"] == 3

    def test_aggregate_calculates_success_rate(self, sample_log_files):
        """Test that success rate is calculated correctly."""
        result = aggregate_results(sample_log_files)

        # N=10: 2/3 success, N=100: 1/2 success
        # Overall: 3/5 = 0.6
        assert abs(result.summary["overall_success_rate"] - 0.6) < 1e-6

    def test_aggregate_empty_list_raises_error(self):
        """Test that aggregating an empty list raises an error."""
        with pytest.raises(ValueError, match="No log files provided"):
            aggregate_results([])

    def test_aggregate_no_valid_runs_raises_error(self, tmp_path):
        """Test that aggregating files with no valid runs raises an error."""
        # Create a log file with no n_value
        data = {
            "method": "symbolic",
            "instances": []
        }
        file_path = tmp_path / "bes_N_invalid.json"
        file_path.write_text(json.dumps(data))

        with pytest.raises(ValueError, match="No valid runs found"):
            aggregate_results([str(file_path)])


class TestSaveResults:
    """Tests for the save_results function."""

    def test_save_results_to_file(self, tmp_path):
        """Test saving results to a file."""
        result = AggregatedResult(
            experiment_id="test_exp",
            method="symbolic",
            runs=[],
            summary={"total_runs": 0},
            metadata={}
        )

        output_path = tmp_path / "results.json"
        success = save_results(result, str(output_path))

        assert success
        assert output_path.exists()

        # Verify content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["experiment_id"] == "test_exp"
        assert saved_data["method"] == "symbolic"

    def test_save_creates_directories(self, tmp_path):
        """Test that saving creates necessary directories."""
        result = AggregatedResult(
            experiment_id="test_exp",
            method="symbolic",
            runs=[],
            summary={},
            metadata={}
        )

        output_path = tmp_path / "subdir" / "nested" / "results.json"
        success = save_results(result, str(output_path))

        assert success
        assert output_path.exists()