"""
Integration test for the logging infrastructure.

This test verifies that the logging system creates the expected log file
and writes an initial timestamped entry. The infrastructure is defined in
``code/utils/logging_config.py``.
"""

import os
import time
from pathlib import Path

import pytest

# Import the function that sets up the full logging stack.
from code.utils.logging_config import initialize_logging, LoggingConfig

@pytest.fixture(scope="function")
def clean_logs():
    """
    Ensure a clean state before each test by removing any existing log files.
    """
    # Define the paths used by the logging configuration.
    run_log = Path("logs/run.log")
    memory_log = Path("logs/memory.log")

    # Remove files if they exist.
    for p in (run_log, memory_log):
        if p.is_file():
            p.unlink()
        # Also remove parent directory if empty to avoid stale state.
        if p.parent.is_dir():
            try:
                p.parent.rmdir()
            except OSError:
                # Directory not empty – leave it.
                pass

    yield  # test runs here

    # Cleanup after test execution.
    for p in (run_log, memory_log):
        if p.is_file():
            p.unlink()
        if p.parent.is_dir():
            try:
                p.parent.rmdir()
            except OSError:
                pass

def test_logging_initializes_and_writes_timestamp(clean_logs):
    """
    Verify that ``initialize_logging`` creates ``logs/run.log`` and writes a
    timestamped log entry containing the phrase ``Logging system initialized``.
    """
    # Use the default configuration; this will create the log file.
    config = LoggingConfig()
    components = initialize_logging(
        log_file=config.log_file,
        level=config.level,
        memory_log_file=config.memory_log_file,
        memory_interval=config.memory_monitor_interval,
        timeout_seconds=config.timeout_seconds,
    )

    # Give the logger a moment to flush the initial entry.
    time.sleep(0.5)

    run_log_path = Path(config.log_file)
    assert run_log_path.is_file(), f"Expected log file {run_log_path} to exist"

    # Read the log content.
    content = run_log_path.read_text(encoding="utf-8")
    assert "Logging system initialized" in content, "Initial log entry missing"

    # The entry should start with a timestamp (e.g., 2026-10-12 14:23:45).
    # We'll check that the first line matches the expected pattern.
    first_line = content.splitlines()[0]
    # Simple pattern: YYYY-MM-DD HH:MM:SS - ...
    import re

    timestamp_regex = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} -"
    assert re.match(timestamp_regex, first_line), f"First log line does not start with a timestamp: {first_line!r}"

    # Clean up background threads started by ``initialize_logging``.
    # The MemoryUsageHandler thread runs as a daemon, but we stop it
    # explicitly to avoid side effects in subsequent tests.
    mem_handler = components.get("memory_handler")
    if mem_handler:
        mem_handler.stop_monitoring()
    timeout_monitor = components.get("timeout_monitor")
    if timeout_monitor:
        # No explicit stop needed; it does not spawn a thread.
        pass

    # Ensure the logger does not retain handlers that could interfere
    # with other tests.
    logger = components.get("logger")
    if logger:
        logger.handlers.clear()