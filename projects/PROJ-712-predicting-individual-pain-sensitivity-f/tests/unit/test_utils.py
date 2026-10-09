"""
Unit tests for the utils module (Task T004).

Verifies:
* Identical files produce identical SHA‑256 hashes via ``compute_checksum``.
* The lightweight logger writes to ``state/log.txt``.
"""

import os
from pathlib import Path

import pytest

# Ensure the project root is on the path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from code.utils import compute_checksum, setup_logging, LOG_FILE, STATE_DIR


def test_compute_checksum_identical_files(tmp_path: Path):
    """
    Two files with the same content must yield the same SHA‑256 hash.
    """
    content = "identical content for checksum test"
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text(content, encoding="utf-8")
    file_b.write_text(content, encoding="utf-8")

    hash_a = compute_checksum(file_a)
    hash_b = compute_checksum(file_b)

    assert hash_a == hash_b, "Hashes for identical files should match"


def test_logger_writes_to_state_log(tmp_path: Path):
    """
    The logger configured by ``setup_logging`` must write messages to
    ``state/log.txt``.
    """
    # Ensure a clean state directory for the test
    # (the utils module creates STATE_DIR on import)
    if LOG_FILE.is_file():
        LOG_FILE.unlink()

    logger = setup_logging("test_logger")
    test_message = "utils unit test log entry"
    logger.info(test_message)

    assert LOG_FILE.is_file(), "Log file was not created"

    log_contents = LOG_FILE.read_text(encoding="utf-8")
    assert test_message in log_contents, "Log entry not found in log file"