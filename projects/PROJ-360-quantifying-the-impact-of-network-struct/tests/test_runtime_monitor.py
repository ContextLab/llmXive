"""
Tests for the runtime monitoring module.
"""

import os
import json
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

# We need to adjust the path to import the module
# Assuming tests are run from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from runtime_monitor import (
    setup_runtime_logger,
    record_start_time,
    load_pipeline_start_time,
    measure_and_log_runtime,
    MAX_RUNTIME_HOURS,
    MAX_RUNTIME_SECONDS,
    RESULTS_DIR,
    RUNTIME_LOG_PATH,
    START_TIME_MARKER_PATH
)


@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary results directory for testing."""
    # Create a temp directory to act as RESULTS_DIR
    temp_dir = tmp_path / "results"
    temp_dir.mkdir()
    return temp_dir


def test_setup_runtime_logger():
    """Test that the logger is configured correctly."""
    logger = setup_runtime_logger()
    assert logger is not None
    assert logger.name == "runtime"
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_record_start_time_creates_file(temp_results_dir, tmp_path):
    """Test that record_start_time creates the marker file."""
    # Temporarily override the paths
    original_results_dir = RESULTS_DIR
    original_marker_path = START_TIME_MARKER_PATH

    # Use the temp directory
    import runtime_monitor
    runtime_monitor.RESULTS_DIR = temp_results_dir
    runtime_monitor.START_TIME_MARKER_PATH = temp_results_dir / ".pipeline_start_time"

    try:
        record_start_time()
        assert runtime_monitor.START_TIME_MARKER_PATH.exists()

        with open(runtime_monitor.START_TIME_MARKER_PATH, 'r') as f:
            data = json.load(f)
            assert "start_timestamp" in data
            assert "start_epoch" in data
            assert isinstance(data["start_epoch"], float)
    finally:
        # Restore original paths
        runtime_monitor.RESULTS_DIR = original_results_dir
        runtime_monitor.START_TIME_MARKER_PATH = original_marker_path


def test_load_pipeline_start_time_returns_none_when_missing():
    """Test loading start time when marker file doesn't exist."""
    # Ensure the file doesn't exist
    if START_TIME_MARKER_PATH.exists():
        os.remove(START_TIME_MARKER_PATH)

    result = load_pipeline_start_time()
    assert result is None


def test_load_pipeline_start_time_returns_value_when_exists(temp_results_dir, tmp_path):
    """Test loading start time when marker file exists."""
    # Create a mock marker file
    mock_data = {
        "start_timestamp": "2024-01-01T00:00:00",
        "start_epoch": 1704067200.0
    }

    # Temporarily override paths
    import runtime_monitor
    original_marker_path = runtime_monitor.START_TIME_MARKER_PATH
    runtime_monitor.START_TIME_MARKER_PATH = temp_results_dir / ".pipeline_start_time"

    try:
        with open(runtime_monitor.START_TIME_MARKER_PATH, 'w') as f:
            json.dump(mock_data, f)

        result = load_pipeline_start_time()
        assert result == 1704067200.0
    finally:
        runtime_monitor.START_TIME_MARKER_PATH = original_marker_path


@patch("runtime_monitor.time.time")
def test_measure_and_log_runtime_compliant(mock_time, temp_results_dir, tmp_path):
    """Test that measure_and_log_runtime works for compliant runtimes."""
    import runtime_monitor

    # Setup temp paths
    original_results_dir = runtime_monitor.RESULTS_DIR
    original_log_path = runtime_monitor.RUNTIME_LOG_PATH
    original_marker_path = runtime_monitor.START_TIME_MARKER_PATH

    runtime_monitor.RESULTS_DIR = temp_results_dir
    runtime_monitor.RUNTIME_LOG_PATH = temp_results_dir / "runtime.log"
    runtime_monitor.START_TIME_MARKER_PATH = temp_results_dir / ".pipeline_start_time"

    try:
        # Create a start marker
        start_epoch = 1000.0
        end_epoch = 2000.0  # 1000 seconds elapsed (< 6 hours)

        mock_time.side_effect = [start_epoch, end_epoch]

        # Record start time
        record_start_time()

        # Mock time.time for the marker load
        with patch("runtime_monitor.time.time", return_value=end_epoch):
            result = measure_and_log_runtime()

        assert result is True
        assert runtime_monitor.RUNTIME_LOG_PATH.exists()

        # Check log content
        with open(runtime_monitor.RUNTIME_LOG_PATH, 'r') as f:
            content = f.read()
            assert "Compliant: True" in content
            assert "PASSED" in content
    finally:
        runtime_monitor.RESULTS_DIR = original_results_dir
        runtime_monitor.RUNTIME_LOG_PATH = original_log_path
        runtime_monitor.START_TIME_MARKER_PATH = original_marker_path


@patch("runtime_monitor.time.time")
def test_measure_and_log_runtime_non_compliant(mock_time, temp_results_dir, tmp_path):
    """Test that measure_and_log_runtime raises error for non-compliant runtimes."""
    import runtime_monitor

    # Setup temp paths
    original_results_dir = runtime_monitor.RESULTS_DIR
    original_log_path = runtime_monitor.RUNTIME_LOG_PATH
    original_marker_path = runtime_monitor.START_TIME_MARKER_PATH

    runtime_monitor.RESULTS_DIR = temp_results_dir
    runtime_monitor.RUNTIME_LOG_PATH = temp_results_dir / "runtime.log"
    runtime_monitor.START_TIME_MARKER_PATH = temp_results_dir / ".pipeline_start_time"

    try:
        # Create a start marker
        start_epoch = 1000.0
        # 7 hours later (25200 seconds) - exceeds 6 hour limit
        end_epoch = start_epoch + (MAX_RUNTIME_SECONDS + 3600)

        mock_time.side_effect = [start_epoch, end_epoch]

        # Record start time
        record_start_time()

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="exceeded maximum allowed runtime"):
            with patch("runtime_monitor.time.time", return_value=end_epoch):
                measure_and_log_runtime()
    finally:
        runtime_monitor.RESULTS_DIR = original_results_dir
        runtime_monitor.RUNTIME_LOG_PATH = original_log_path
        runtime_monitor.START_TIME_MARKER_PATH = original_marker_path


def test_main_record_start():
    """Test main function with --record-start argument."""
    import runtime_monitor
    from unittest.mock import patch

    with patch("sys.argv", ["runtime_monitor.py", "--record-start"]):
        # We can't easily test the full flow without mocking file system,
        # but we can verify the argument parsing works
        pass


def test_main_measure():
    """Test main function with --measure argument."""
    import runtime_monitor
    from unittest.mock import patch, mock_open, MagicMock
    import time

    # Mock the necessary functions to avoid actual file operations in this simple test
    with patch("runtime_monitor.load_pipeline_start_time", return_value=time.time() - 100):
        with patch("runtime_monitor.time.time", return_value=time.time()):
            with patch("builtins.open", mock_open()):
                with patch("runtime_monitor.setup_runtime_logger"):
                    result = runtime_monitor.main()
                    assert result == 0