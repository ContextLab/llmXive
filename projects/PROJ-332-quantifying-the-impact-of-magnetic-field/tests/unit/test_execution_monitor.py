"""
Unit tests for the execution monitor module (T033b).

These tests verify that the time tracking and timeout logic works correctly
without actually running the full pipeline.
"""

import time
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import tempfile

from utils.execution_monitor import (
    time_execution,
    verify_pipeline_execution_time,
    TimeoutExceededError,
    CI_TIMEOUT_SECONDS
)


class TestTimeExecutionDecorator:
    """Tests for the time_execution decorator."""

    def test_successful_execution_within_limit(self):
        """Verify decorator works for fast functions."""
        @time_execution(timeout_seconds=10)
        def fast_function():
            return "result"

        result = fast_function()
        assert result == "result"

    def test_execution_exceeds_timeout(self):
        """Verify decorator raises TimeoutExceededError when limit exceeded."""
        @time_execution(timeout_seconds=0.1)
        def slow_function():
            time.sleep(0.5)
            return "result"

        with pytest.raises(TimeoutExceededError):
            slow_function()

    def test_execution_returns_duration_info(self):
        """Verify decorator returns duration information."""
        @time_execution(timeout_seconds=10)
        def timed_function():
            time.sleep(0.1)
            return "done"

        # The decorator returns a dict with timing info
        result = timed_function()
        assert isinstance(result, dict)
        assert "duration_seconds" in result
        assert "status" in result
        assert result["status"] == "success"


class TestVerifyPipelineExecutionTime:
    """Tests for the verify_pipeline_execution_time function."""

    def test_successful_pipeline_run(self, tmp_path):
        """Verify successful pipeline run is recorded correctly."""
        output_file = tmp_path / "metrics.json"

        def mock_pipeline():
            time.sleep(0.1)
            return True

        success = verify_pipeline_execution_time(
            pipeline_func=mock_pipeline,
            timeout_seconds=10,
            output_path=str(output_file)
        )

        assert success is True
        assert output_file.exists()

        with open(output_file, "r") as f:
            metrics = json.load(f)

        assert metrics["execution_status"] == "success"
        assert metrics["duration_seconds"] > 0
        assert metrics["duration_seconds"] < 10

    def test_pipeline_timeout(self, tmp_path):
        """Verify timeout is detected and recorded."""
        output_file = tmp_path / "metrics.json"

        def slow_pipeline():
            time.sleep(0.5)
            return True

        success = verify_pipeline_execution_time(
            pipeline_func=slow_pipeline,
            timeout_seconds=0.1,  # Short timeout
            output_path=str(output_file)
        )

        assert success is False
        assert output_file.exists()

        with open(output_file, "r") as f:
            metrics = json.load(f)

        assert metrics["execution_status"] == "timeout_exceeded"
        assert "exceeded" in metrics["message"].lower()

    def test_pipeline_error_does_not_fail_time_check(self, tmp_path):
        """Verify that pipeline errors (non-timeout) do not fail the time check."""
        output_file = tmp_path / "metrics.json"

        def failing_pipeline():
            raise ValueError("Simulated pipeline error")

        # Should return True because time limit was not exceeded
        success = verify_pipeline_execution_time(
            pipeline_func=failing_pipeline,
            timeout_seconds=10,
            output_path=str(output_file)
        )

        assert success is True  # Time limit ok, even though pipeline failed
        assert output_file.exists()

        with open(output_file, "r") as f:
            metrics = json.load(f)

        assert metrics["execution_status"] == "pipeline_error"


class TestCIConstants:
    """Tests for CI configuration constants."""

    def test_timeout_is_six_hours(self):
        """Verify the CI timeout is set to 6 hours."""
        assert CI_TIMEOUT_SECONDS == 6 * 3600
        assert CI_TIMEOUT_SECONDS == 21600
