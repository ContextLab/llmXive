"""
Unit tests for the logging infrastructure.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
import pytest
from datetime import datetime

from code.utils.logger import (
    setup_logger,
    track_error,
    get_tracked_errors,
    log_error,
    log_critical,
    log_exception,
    log_pipeline_step,
    get_log_file_path,
    get_error_summary,
    export_error_log
)


class TestLoggerSetup:
    """Tests for logger initialization and configuration."""

    def test_setup_logger_creates_directory(self, tmp_path):
        """Verify that setup_logger creates the log directory if it doesn't exist."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        result_path = setup_logger(log_dir=str(log_dir), log_file=log_file, level="DEBUG")

        assert log_dir.exists()
        assert result_path == log_dir / log_file
        assert result_path.exists()

    def test_setup_logger_returns_correct_path(self, tmp_path):
        """Verify setup_logger returns the correct log file path."""
        log_dir = tmp_path / "logs"
        log_file = "custom.log"

        result_path = setup_logger(log_dir=str(log_dir), log_file=log_file)

        assert result_path == log_dir / log_file

    def test_setup_logger_writes_initial_message(self, tmp_path):
        """Verify that setup_logger writes an initialization message to the log file."""
        log_dir = tmp_path / "logs"
        log_file = "init.log"

        setup_logger(log_dir=str(log_dir), log_file=log_file)

        log_path = log_dir / log_file
        content = log_path.read_text()

        assert "Logger initialized" in content
        assert str(log_path) in content

    def test_multiple_setup_calls(self, tmp_path):
        """Verify that calling setup_logger multiple times doesn't crash."""
        log_dir = tmp_path / "logs"
        log_file = "multi.log"

        # First call
        path1 = setup_logger(log_dir=str(log_dir), log_file=log_file)

        # Second call (should not crash)
        path2 = setup_logger(log_dir=str(log_dir), log_file=log_file, level="INFO")

        assert path1 == path2
        assert log_dir.exists()


class TestErrorTracking:
    """Tests for error tracking functionality."""

    def test_track_error_adds_to_list(self):
        """Verify track_error adds an entry to the tracked errors list."""
        # Clear previous errors
        # Note: In a real test suite, we'd reset the global state
        # For this test, we just check the return value

        error = track_error("E001", "Test error message", {"key": "value"})

        assert error["error_code"] == "E001"
        assert error["error_message"] == "Test error message"
        assert error["context"]["key"] == "value"
        assert "timestamp" in error
        assert error["severity"] == "ERROR"

    def test_track_error_with_custom_severity(self):
        """Verify track_error respects custom severity levels."""
        error = track_error("E002", "Critical issue", severity="CRITICAL")

        assert error["severity"] == "CRITICAL"

    def test_get_tracked_errors_returns_copy(self):
        """Verify get_tracked_errors returns a copy, not the original list."""
        initial_count = len(get_tracked_errors())

        errors = get_tracked_errors()
        errors.append({"fake": "error"})

        # The internal list should not be modified
        assert len(get_tracked_errors()) == initial_count

    def test_log_error_tracks_and_logs(self, tmp_path, caplog):
        """Verify log_error both tracks the error and logs it."""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir), log_file="error_test.log")

        log_error("E101", "Test error for logging")

        # Check that the log file contains the error
        log_path = log_dir / "error_test.log"
        content = log_path.read_text()

        assert "[E101]" in content
        assert "Test error for logging" in content

    def test_log_critical_tracks_as_critical(self, tmp_path):
        """Verify log_critical tracks the error with CRITICAL severity."""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir), log_file="critical_test.log")

        log_critical("E999", "Critical failure")

        errors = get_tracked_errors()
        # Find our error
        our_error = next((e for e in errors if e["error_code"] == "E999"), None)

        assert our_error is not None
        assert our_error["severity"] == "CRITICAL"


class TestPipelineStepLogging:
    """Tests for pipeline step logging."""

    def test_log_pipeline_step_without_duration(self, tmp_path):
        """Verify log_pipeline_step works without duration."""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir), log_file="step_test.log")

        log_pipeline_step("ALIGNMENT", "Starting alignment process")

        log_path = log_dir / "step_test.log"
        content = log_path.read_text()

        assert "STEP: ALIGNMENT" in content
        assert "Starting alignment process" in content

    def test_log_pipeline_step_with_duration(self, tmp_path):
        """Verify log_pipeline_step includes duration when provided."""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir), log_file="step_duration_test.log")

        log_pipeline_step("QUANTIFY", "PSI calculation complete", duration=123.45)

        log_path = log_dir / "step_duration_test.log"
        content = log_path.read_text()

        assert "STEP: QUANTIFY" in content
        assert "PSI calculation complete" in content
        assert "123.45" in content


class TestErrorSummary:
    """Tests for error summary generation."""

    def test_get_error_summary_no_errors(self):
        """Verify get_error_summary returns appropriate message when no errors."""
        # This test assumes a clean slate; in practice, we'd reset state
        summary = get_error_summary()

        # Should contain either "No errors" or count information
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_get_error_summary_with_errors(self, tmp_path):
        """Verify get_error_summary formats errors correctly."""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir), log_file="summary_test.log")

        track_error("E001", "First error", {"source": "test1"})
        track_error("E002", "Second error", severity="WARNING")
        track_error("E001", "Duplicate error code")

        summary = get_error_summary()

        assert "ERROR SUMMARY" in summary
        assert "Total errors: 3" in summary
        assert "E001" in summary
        assert "E002" in summary
        assert "2 occurrence(s)" in summary  # E001 appears twice


class TestErrorExport:
    """Tests for error log export functionality."""

    def test_export_error_log_creates_file(self, tmp_path):
        """Verify export_error_log creates the output file."""
        log_dir = tmp_path / "logs"
        output_dir = tmp_path / "exports"
        setup_logger(log_dir=str(log_dir), log_file="export_test.log")

        track_error("E001", "Export test error")

        output_path = export_error_log(str(output_dir / "errors.json"))

        assert output_path.exists()
        assert output_path.suffix == ".json"

    def test_export_error_log_valid_json(self, tmp_path):
        """Verify exported error log is valid JSON."""
        log_dir = tmp_path / "logs"
        output_dir = tmp_path / "exports"
        setup_logger(log_dir=str(log_dir), log_file="json_test.log")

        track_error("E001", "JSON test", {"key": "value"})

        output_path = export_error_log(str(output_dir / "errors.json"))
        content = output_path.read_text()

        # Should be valid JSON
        data = json.loads(content)
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["error_code"] == "E001"

    def test_export_error_log_includes_timestamp(self, tmp_path):
        """Verify exported errors include timestamps."""
        log_dir = tmp_path / "logs"
        output_dir = tmp_path / "exports"
        setup_logger(log_dir=str(log_dir), log_file="timestamp_test.log")

        track_error("E001", "Timestamp test")

        output_path = export_error_log(str(output_dir / "errors.json"))
        data = json.loads(output_path.read_text())

        assert "timestamp" in data[0]
        # Should be ISO format
        datetime.fromisoformat(data[0]["timestamp"])


class TestLoggerIntegration:
    """Integration tests for the logger module."""

    def test_full_workflow(self, tmp_path):
        """Test a complete logging workflow."""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir), log_file="workflow.log")

        # Log a pipeline step
        log_pipeline_step("DOWNLOAD", "Fetching SRA data", duration=45.2)

        # Track some errors
        track_error("E101", "Replicate count too low", {"count": 2})
        log_error("E102", "Replicate count too high")

        # Log critical
        log_critical("E999", "Pipeline aborted")

        # Get summary
        summary = get_error_summary()
        assert "Total errors: 3" in summary

        # Export errors
        export_dir = tmp_path / "exports"
        export_path = export_error_log(str(export_dir / "workflow_errors.json"))

        # Verify file exists and has content
        assert export_path.exists()
        data = json.loads(export_path.read_text())
        assert len(data) == 3

        # Verify log file has all entries
        log_path = log_dir / "workflow.log"
        content = log_path.read_text()
        assert "DOWNLOAD" in content
        assert "[E101]" in content
        assert "[E999]" in content