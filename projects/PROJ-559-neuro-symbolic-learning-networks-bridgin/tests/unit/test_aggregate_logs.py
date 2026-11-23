"""
Unit tests for log aggregation functionality (T022).

Tests:
- load_simulation_logs
- normalize_log_fields
- validate_log
- write_simulation_logs_csv
- aggregate_logs
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulate.aggregate_logs import (
    load_simulation_logs,
    normalize_log_fields,
    validate_log,
    write_simulation_logs_csv,
    aggregate_logs,
    REQUIRED_FIELDS
)


class TestLoadSimulationLogs:
    def test_load_from_valid_directory(self, tmp_path):
        """Test loading logs from a directory with valid JSON files."""
        # Create test logs
        log1 = {"student_id": "s1", "problem_id": "p1", "condition": "neural", "correct": 1}
        log2 = {"student_id": "s2", "problem_id": "p1", "condition": "symbolic", "correct": 0}

        log_file1 = tmp_path / "log1.json"
        log_file2 = tmp_path / "log2.json"

        with open(log_file1, 'w') as f:
            json.dump(log1, f)
        with open(log_file2, 'w') as f:
            json.dump(log2, f)

        logs = load_simulation_logs(tmp_path)

        assert len(logs) == 2
        assert logs[0]["student_id"] == "s1"
        assert logs[1]["condition"] == "symbolic"

    def test_load_from_empty_directory(self, tmp_path):
        """Test loading from directory with no JSON files."""
        logs = load_simulation_logs(tmp_path)
        assert logs == []

    def test_load_handles_invalid_json(self, tmp_path):
        """Test that invalid JSON files are skipped with warning."""
        valid_log = {"student_id": "s1", "problem_id": "p1", "condition": "neural", "correct": 1}
        invalid_log = "{ invalid json }"

        valid_file = tmp_path / "valid.json"
        invalid_file = tmp_path / "invalid.json"

        with open(valid_file, 'w') as f:
            json.dump(valid_log, f)
        with open(invalid_file, 'w') as f:
            f.write(invalid_log)

        logs = load_simulation_logs(tmp_path)

        # Should load only the valid log
        assert len(logs) == 1
        assert logs[0]["student_id"] == "s1"


class TestNormalizeLogFields:
    def test_normalize_standard_fields(self):
        """Test normalization with standard field names."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1,
            "response_time_seconds": 2.5,
            "comprehension_rating": 4,
            "timestamp": "2024-01-01T00:00:00Z"
        }

        normalized = normalize_log_fields(log)

        assert normalized["student_id"] == "s1"
        assert normalized["condition"] == "neural"
        assert normalized["data_source"] == "simulated"  # Default

    def test_normalize_field_variations(self):
        """Test normalization with alternative field names."""
        log = {
            "studentId": "s2",
            "problemId": "p2",
            "experiment_condition": "symbolic",
            "is_correct": 0,
            "rt_seconds": 3.0,
            "comprehension": 3
        }

        normalized = normalize_log_fields(log)

        assert normalized["student_id"] == "s2"
        assert normalized["problem_id"] == "p2"
        assert normalized["condition"] == "symbolic"
        assert normalized["correct"] == 0
        assert normalized["response_time_seconds"] == 3.0
        assert normalized["comprehension_rating"] == 3

    def test_normalize_clamps_comprehension_rating(self):
        """Test that comprehension rating is clamped to 1-5."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1,
            "comprehension_rating": 10  # Out of range
        }

        normalized = normalize_log_fields(log)
        assert normalized["comprehension_rating"] == 5

        log["comprehension_rating"] = 0
        normalized = normalize_log_fields(log)
        assert normalized["comprehension_rating"] == 1

    def test_normalize_handles_missing_data_source(self):
        """Test that data_source defaults to 'simulated'."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1
        }

        normalized = normalize_log_fields(log)
        assert normalized["data_source"] == "simulated"


class TestValidateLog:
    def test_valid_log(self):
        """Test validation of a complete, valid log."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1,
            "response_time_seconds": 2.5,
            "comprehension_rating": 3,
            "data_source": "simulated",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        assert validate_log(log) is True

    def test_invalid_condition(self):
        """Test validation fails for invalid condition."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "invalid_condition",
            "correct": 1,
            "response_time_seconds": 2.5,
            "comprehension_rating": 3,
            "data_source": "simulated",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        assert validate_log(log) is False

    def test_invalid_correct_value(self):
        """Test validation fails for non-binary correct value."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 2,
            "response_time_seconds": 2.5,
            "comprehension_rating": 3,
            "data_source": "simulated",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        assert validate_log(log) is False

    def test_invalid_comprehension_rating(self):
        """Test validation fails for out-of-range comprehension rating."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1,
            "response_time_seconds": 2.5,
            "comprehension_rating": 6,
            "data_source": "simulated",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        assert validate_log(log) is False

    def test_missing_required_field(self):
        """Test validation fails for missing required field."""
        log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1,
            "response_time_seconds": 2.5,
            "comprehension_rating": 3,
            "data_source": "simulated"
            # Missing timestamp
        }

        assert validate_log(log) is False


class TestWriteSimulationLogsCSV:
    def test_write_csv_creates_file(self, tmp_path):
        """Test that CSV file is created with correct headers."""
        output_path = tmp_path / "output.csv"
        logs = [
            {
                "student_id": "s1",
                "problem_id": "p1",
                "condition": "neural",
                "correct": 1,
                "response_time_seconds": 2.5,
                "comprehension_rating": 3,
                "data_source": "simulated",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]

        write_simulation_logs_csv(logs, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            header = f.readline().strip()
            assert header == ",".join(REQUIRED_FIELDS)

    def test_write_csv_multiple_records(self, tmp_path):
        """Test writing multiple records to CSV."""
        output_path = tmp_path / "output.csv"
        logs = [
            {
                "student_id": "s1",
                "problem_id": "p1",
                "condition": "neural",
                "correct": 1,
                "response_time_seconds": 2.5,
                "comprehension_rating": 3,
                "data_source": "simulated",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "student_id": "s2",
                "problem_id": "p2",
                "condition": "symbolic",
                "correct": 0,
                "response_time_seconds": 3.0,
                "comprehension_rating": 4,
                "data_source": "simulated",
                "timestamp": "2024-01-01T00:00:01Z"
            }
        ]

        write_simulation_logs_csv(logs, output_path)

        with open(output_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3  # Header + 2 records


class TestAggregateLogs:
    def test_aggregate_logs_full_pipeline(self, tmp_path):
        """Test the full aggregation pipeline: load -> normalize -> validate -> write."""
        # Create test logs
        log1 = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1,
            "response_time_seconds": 2.5,
            "comprehension_rating": 3,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        log2 = {
            "student_id": "s2",
            "problem_id": "p2",
            "condition": "symbolic",
            "correct": 0,
            "response_time_seconds": 3.0,
            "comprehension_rating": 4,
            "timestamp": "2024-01-01T00:00:01Z"
        }

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        with open(logs_dir / "log1.json", 'w') as f:
            json.dump(log1, f)
        with open(logs_dir / "log2.json", 'w') as f:
            json.dump(log2, f)

        output_path = tmp_path / "output.csv"

        count = aggregate_logs(logs_dir, output_path)

        assert count == 2
        assert output_path.exists()

    def test_aggregate_logs_skips_invalid(self, tmp_path):
        """Test that invalid logs are skipped during aggregation."""
        valid_log = {
            "student_id": "s1",
            "problem_id": "p1",
            "condition": "neural",
            "correct": 1,
            "response_time_seconds": 2.5,
            "comprehension_rating": 3,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        invalid_log = {
            "student_id": "s2",
            "problem_id": "p2",
            "condition": "invalid",  # Invalid condition
            "correct": 0,
            "response_time_seconds": 3.0,
            "comprehension_rating": 4,
            "timestamp": "2024-01-01T00:00:01Z"
        }

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        with open(logs_dir / "valid.json", 'w') as f:
            json.dump(valid_log, f)
        with open(logs_dir / "invalid.json", 'w') as f:
            json.dump(invalid_log, f)

        output_path = tmp_path / "output.csv"

        count = aggregate_logs(logs_dir, output_path)

        assert count == 1  # Only valid log should be written