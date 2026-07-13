"""
Unit tests for the scheduler trace schema and initialization.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from utils.scheduler_trace_schema import (
    validate_trace_entry,
    VALID_EVENT_TYPES,
    SCHEMA_DEFINITION
)
from utils.initialize_trace import initialize_trace_file


class TestSchemaValidation:
    """Tests for schema validation logic."""

    def test_valid_phase1_entry(self):
        """Test validation of a valid Phase 1 selection entry."""
        entry = {
            "timestamp": "2023-10-27T10:00:00+00:00",
            "event": "phase1_selection",
            "data": {
                "low_coverage_states_count": 6,
                "selected_tasks_count": 2,
                "threshold": 0.05
            }
        }
        assert validate_trace_entry(entry) is True

    def test_valid_phase2_entry(self):
        """Test validation of a valid Phase 2 selection entry."""
        entry = {
            "timestamp": "2023-10-27T10:00:01+00:00",
            "event": "phase2_selection",
            "data": {
                "range": [0.1, 0.9],
                "target": 0.5,
                "selected_tasks_count": 1
            }
        }
        assert validate_trace_entry(entry) is True

    def test_valid_metrics_triggered_entry(self):
        """Test validation of a metrics_triggered entry."""
        entry = {
            "timestamp": "2023-10-27T10:00:02+00:00",
            "event": "metrics_triggered",
            "data": {
                "state_variable": "dark_mode",
                "transition": "false_to_true",
                "task_id": "task_123"
            }
        }
        assert validate_trace_entry(entry) is True

    def test_missing_timestamp(self):
        """Test that missing timestamp fails validation."""
        entry = {
            "event": "phase1_selection",
            "data": {}
        }
        assert validate_trace_entry(entry) is False

    def test_missing_event(self):
        """Test that missing event fails validation."""
        entry = {
            "timestamp": "2023-10-27T10:00:00+00:00",
            "data": {}
        }
        assert validate_trace_entry(entry) is False

    def test_missing_data(self):
        """Test that missing data fails validation."""
        entry = {
            "timestamp": "2023-10-27T10:00:00+00:00",
            "event": "phase1_selection"
        }
        assert validate_trace_entry(entry) is False

    def test_invalid_event_type(self):
        """Test that invalid event type fails validation."""
        entry = {
            "timestamp": "2023-10-27T10:00:00+00:00",
            "event": "invalid_event",
            "data": {}
        }
        assert validate_trace_entry(entry) is False

    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp format fails validation."""
        entry = {
            "timestamp": "not-a-date",
            "event": "phase1_selection",
            "data": {}
        }
        assert validate_trace_entry(entry) is False

    def test_data_not_object(self):
        """Test that data as non-object fails validation."""
        entry = {
            "timestamp": "2023-10-27T10:00:00+00:00",
            "event": "phase1_selection",
            "data": "string_instead_of_object"
        }
        assert validate_trace_entry(entry) is False

class TestTraceInitialization:
    """Tests for trace file initialization."""

    def test_creates_file_and_directory(self):
        """Test that initialization creates the file and parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data" / "processed" / "test_trace.json"
            initialize_trace_file(output_path)
            assert output_path.exists()

    def test_file_contains_schema_entry(self):
        """Test that the initialized file contains a schema definition entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data" / "processed" / "test_trace.json"
            initialize_trace_file(output_path)

            with open(output_path, 'r', encoding='utf-8') as f:
                line = f.readline()
                entry = json.loads(line)

            assert entry["event"] == "schema_definition"
            assert "version" in entry["data"]
            assert "schema" in entry["data"]
            assert "description" in entry["data"]

    def test_file_is_valid_jsonl(self):
        """Test that the initialized file contains valid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data" / "processed" / "test_trace.json"
            initialize_trace_file(output_path)

            with open(output_path, 'r', encoding='utf-8') as f:
                for line in f:
                    json.loads(line)  # Should not raise

class TestValidEventTypes:
    """Tests for the list of valid event types."""

    def test_all_expected_events_present(self):
        """Test that all expected event types are in the list."""
        expected_events = [
            "phase1_selection",
            "phase2_selection",
            "fallback_entropy",
            "fallback_random",
            "deadlock_prevention",
            "metrics_triggered",
            "error_encountered"
        ]
        for event in expected_events:
            assert event in VALID_EVENT_TYPES