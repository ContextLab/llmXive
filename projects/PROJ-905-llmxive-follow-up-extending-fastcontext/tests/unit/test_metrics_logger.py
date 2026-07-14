"""Unit tests for metrics_logger module.

Tests the validation and logging functionality for experiment metrics.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from metrics_logger import (
    REQUIRED_FIELDS,
    create_log_entry,
    log_metrics,
    validate_log,
)


class TestValidateLog:
    """Tests for the validate_log function."""

    def test_valid_log_with_all_required_fields(self):
        """Test that a log with all required fields passes validation."""
        valid_log = {
            "context_precision": 0.85,
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }
        assert validate_log(valid_log) is True

    def test_missing_context_precision(self):
        """Test that missing context_precision fails validation."""
        invalid_log = {
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }
        assert validate_log(invalid_log) is False

    def test_missing_total_tokens(self):
        """Test that missing total_tokens fails validation."""
        invalid_log = {
            "context_precision": 0.85,
            "wall_clock_latency": 2.5,
        }
        assert validate_log(invalid_log) is False

    def test_missing_wall_clock_latency(self):
        """Test that missing wall_clock_latency fails validation."""
        invalid_log = {
            "context_precision": 0.85,
            "total_tokens": 1024,
        }
        assert validate_log(invalid_log) is False

    def test_invalid_type_context_precision(self):
        """Test that wrong type for context_precision fails validation."""
        invalid_log = {
            "context_precision": "high",  # Should be float/int
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }
        assert validate_log(invalid_log) is False

    def test_invalid_type_total_tokens(self):
        """Test that wrong type for total_tokens fails validation."""
        invalid_log = {
            "context_precision": 0.85,
            "total_tokens": "many",  # Should be int
            "wall_clock_latency": 2.5,
        }
        assert validate_log(invalid_log) is False

    def test_invalid_type_wall_clock_latency(self):
        """Test that wrong type for wall_clock_latency fails validation."""
        invalid_log = {
            "context_precision": 0.85,
            "total_tokens": 1024,
            "wall_clock_latency": "fast",  # Should be float/int
        }
        assert validate_log(invalid_log) is False

    def test_negative_total_tokens(self):
        """Test that negative total_tokens fails validation."""
        invalid_log = {
            "context_precision": 0.85,
            "total_tokens": -100,
            "wall_clock_latency": 2.5,
        }
        assert validate_log(invalid_log) is False

    def test_negative_wall_clock_latency(self):
        """Test that negative wall_clock_latency fails validation."""
        invalid_log = {
            "context_precision": 0.85,
            "total_tokens": 1024,
            "wall_clock_latency": -1.0,
        }
        assert validate_log(invalid_log) is False

    def test_non_dict_input(self):
        """Test that non-dict input fails validation."""
        assert validate_log("not a dict") is False
        assert validate_log(["not", "a", "dict"]) is False
        assert validate_log(None) is False

    def test_extra_fields_allowed(self):
        """Test that extra fields don't cause validation failure."""
        valid_log = {
            "context_precision": 0.85,
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
            "extra_field": "allowed",
            "repo_id": "test-repo",
        }
        assert validate_log(valid_log) is True

    def test_integer_context_precision(self):
        """Test that integer context_precision is accepted."""
        valid_log = {
            "context_precision": 1,  # Integer instead of float
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }
        assert validate_log(valid_log) is True

class TestCreateLogEntry:
    """Tests for the create_log_entry function."""

    def test_minimal_entry(self):
        """Test creating a minimal log entry with required fields only."""
        entry = create_log_entry(
            context_precision=0.9,
            total_tokens=512,
            wall_clock_latency=1.0,
        )
        assert "timestamp" in entry
        assert entry["context_precision"] == 0.9
        assert entry["total_tokens"] == 512
        assert entry["wall_clock_latency"] == 1.0
        assert validate_log(entry) is True

    def test_entry_with_optional_fields(self):
        """Test creating an entry with all optional fields."""
        entry = create_log_entry(
            context_precision=0.9,
            total_tokens=512,
            wall_clock_latency=1.0,
            repo_id="my-repo",
            issue_id="42",
            model_name="fastcontext-lite",
        )
        assert entry["repo_id"] == "my-repo"
        assert entry["issue_id"] == "42"
        assert entry["model_name"] == "fastcontext-lite"
        assert validate_log(entry) is True

    def test_entry_with_extra_fields(self):
        """Test creating an entry with extra custom fields."""
        extra = {"custom_metric": 0.75, "version": "1.0"}
        entry = create_log_entry(
            context_precision=0.9,
            total_tokens=512,
            wall_clock_latency=1.0,
            extra=extra,
        )
        assert entry["custom_metric"] == 0.75
        assert entry["version"] == "1.0"
        assert validate_log(entry) is True

    def test_invalid_values_raise_error(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError):
            create_log_entry(
                context_precision="invalid",
                total_tokens=512,
                wall_clock_latency=1.0,
            )

class TestLogMetrics:
    """Tests for the log_metrics function."""

    def test_log_metrics_creates_file(self):
        """Test that log_metrics creates the output file."""
        entry = {
            "context_precision": 0.85,
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_logs.jsonl"
            result_path = log_metrics(entry, output_path, append=False)

            assert result_path == output_path
            assert output_path.exists()

            with open(output_path, "r") as f:
                content = f.read().strip()
                parsed = json.loads(content)
                assert parsed["context_precision"] == 0.85

    def test_log_metrics_appends(self):
        """Test that log_metrics appends when append=True."""
        entry1 = {
            "context_precision": 0.85,
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }
        entry2 = {
            "context_precision": 0.90,
            "total_tokens": 2048,
            "wall_clock_latency": 3.0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_logs.jsonl"

            log_metrics(entry1, output_path, append=False)
            log_metrics(entry2, output_path, append=True)

            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2

    def test_log_metrics_invalid_entry_raises(self):
        """Test that logging an invalid entry raises ValueError."""
        invalid_entry = {
            "context_precision": "invalid",
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_logs.jsonl"
            with pytest.raises(ValueError):
                log_metrics(invalid_entry, output_path)

    def test_log_metrics_creates_directories(self):
        """Test that log_metrics creates parent directories."""
        entry = {
            "context_precision": 0.85,
            "total_tokens": 1024,
            "wall_clock_latency": 2.5,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "logs.jsonl"
            result_path = log_metrics(entry, nested_path, append=False)

            assert result_path == nested_path
            assert result_path.exists()

class TestRequiredFields:
    """Tests for the REQUIRED_FIELDS constant."""

    def test_required_fields_structure(self):
        """Test that REQUIRED_FIELDS has the expected structure."""
        assert "context_precision" in REQUIRED_FIELDS
        assert "total_tokens" in REQUIRED_FIELDS
        assert "wall_clock_latency" in REQUIRED_FIELDS

        assert isinstance(REQUIRED_FIELDS["context_precision"], tuple)
        assert isinstance(REQUIRED_FIELDS["total_tokens"], tuple)
        assert isinstance(REQUIRED_FIELDS["wall_clock_latency"], tuple)

    def test_required_fields_types(self):
        """Test that required fields accept correct types."""
        assert float in REQUIRED_FIELDS["context_precision"]
        assert int in REQUIRED_FIELDS["context_precision"]
        assert int in REQUIRED_FIELDS["total_tokens"]
        assert float in REQUIRED_FIELDS["wall_clock_latency"]
        assert int in REQUIRED_FIELDS["wall_clock_latency"]