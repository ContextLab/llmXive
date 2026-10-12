"""
Unit tests for the utils module (Task T004).

Verifies:
* Identical files produce identical SHA‑256 hashes via ``compute_checksum``.
* The lightweight logger writes timestamped entries to ``artifacts/log.txt``.
* ``record_artifact_hash`` computes a SHA‑256 hash and RETURNS it.
"""

import hashlib
import os
from pathlib import Path
import pytest

# Ensure the project root is on the path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from code.utils import (
    compute_checksum,
    setup_logging,
    record_artifact_hash,
    set_global_seed,
    LOG_FILE,
)

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
    assert hash_a == hashlib.sha256(content.encode("utf-8")).hexdigest()

def test_logger_writes_to_project_log(tmp_path: Path):
    """
    The logger configured by ``setup_logging`` must write messages to
    ``artifacts/log.txt`` with a timestamp.
    """
    # Ensure a clean log file for the test
    if LOG_FILE.is_file():
        LOG_FILE.unlink()

    logger = setup_logging("test_logger")
    test_message = "utils unit test log entry"
    logger.info(test_message)

    assert LOG_FILE.is_file(), "Log file was not created"

    log_contents = LOG_FILE.read_text(encoding="utf-8")
    assert test_message in log_contents, "Log entry not found in log file"
    # Timestamped entry: 'YYYY-MM-DD HH:MMSS,mmm - name - LEVEL - msg'
    assert " - test_logger - INFO - " in log_contents

def test_record_artifact_hash_returns_hash(tmp_path: Path):
    """
    ``record_artifact_hash`` must compute the SHA‑256 hash of the file
    and RETURN the hex digest to the caller.
    """
    content = "artifact content to hash"
    target = tmp_path / "artifact.csv"
    target.write_text(content, encoding="utf-8")

    state_file = tmp_path / "hashes.yaml"
    returned = record_artifact_hash(target, state_file=state_file)

    expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert isinstance(returned, str)
    assert returned == expected, (
        "record_artifact_hash must return the SHA‑256 hex digest of the file"
    )

    # Two identical files must yield identical returned hashes
    other = tmp_path / "artifact_copy.csv"
    other.write_text(content, encoding="utf-8")
    assert record_artifact_hash(other, state_file=state_file) == returned

def test_set_global_seed_deterministic():
    """Seed pinning must make random draws reproducible."""
    import random

    set_global_seed(42)
    a = [random.random() for _ in range(5)]
    set_global_seed(42)
    b = [random.random() for _ in range(5)]
    assert a == b

    try:
        import numpy as np
        set_global_seed(42)
        x = np.random.rand(5)
        set_global_seed(42)
        y = np.random.rand(5)
        assert (x == y).all()
    except ImportError:
        pass