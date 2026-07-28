"""Unit test for logger extension.

This test verifies that the logger records the required ``command``,
``versions`` and ``seed`` fields in each JSON‑Line entry written to the
pipeline log file.  It replaces the logger's file handler with a temporary
file to avoid polluting the real ``pipeline.log`` used by the pipeline.
"""

import json
import logging
from pathlib import Path

import pytest

from src.utils.logger import get_logger, log_cli_invocation


@pytest.fixture
def temp_logger(tmp_path: Path):
    """Replace the logger's FileHandler with one that writes to a temporary file."""
    logger = get_logger()

    # Remove existing FileHandler(s) to avoid writing to the real log.
    for handler in list(logger.handlers):
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # Create a new temporary log file.
    log_file = tmp_path / "pipeline.log"
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")

    # Preserve the original formatter if any.
    if logger.handlers:
        # Use the formatter from the first remaining handler (if any).
        formatter = logger.handlers[0].formatter
    else:
        # Fallback to a simple formatter; the actual logger uses JSONFormatter,
        # but the test only needs to be able to read JSON lines.
        formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Ensure the logger propagates messages.
    logger.propagate = False

    yield logger, log_file

    # Clean up: remove the temporary handler.
    logger.removeHandler(file_handler)


def test_logger_extension_contains_fields(temp_logger):
    """Check that a log entry created via ``log_cli_invocation`` contains the
    required fields as defined in the schema."""
    logger, log_file = temp_logger

    # Example data to log.
    command = "run_pipeline --threshold 0.85 --seed 12345"
    versions = {"python": "3.11.8", "numpy": "1.26.2", "pandas": "2.2.0"}
    seed = 12345

    # Emit the log entry.
    log_cli_invocation(command, versions, seed)

    # Read the last line from the temporary log file.
    with log_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    assert lines, "The log file should contain at least one entry."

    # The logger writes JSON Lines; parse the most recent entry.
    entry = json.loads(lines[-1].strip())

    # Verify required fields are present and correctly recorded.
    assert "command" in entry, "Log entry missing required 'command' field."
    assert entry["command"] == command, "Logged command does not match input."

    assert "versions" in entry, "Log entry missing required 'versions' field."
    assert entry["versions"] == versions, "Logged versions do not match input."

    assert "seed" in entry, "Log entry missing required 'seed' field."
    assert entry["seed"] == seed, "Logged seed does not match input."