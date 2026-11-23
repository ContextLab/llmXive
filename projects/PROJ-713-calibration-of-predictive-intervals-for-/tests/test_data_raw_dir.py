"""
Unit test for task T001c – verifies that the `data/raw/` directory can be
created idempotently and is writable.
"""

import os
from pathlib import Path

from llmxive_toolkit import paths
from code.create_data_raw_dir import create_and_verify_data_raw_dir


def test_idempotent_creation_of_data_raw_dir():
    """
    Call the creation function twice to ensure idempotency, then check that
    the directory exists and is writable.
    """
    # First call – should create the directory.
    create_and_verify_data_raw_dir()
    # Second call – should be a no‑op and not raise.
    create_and_verify_data_raw_dir()

    raw_dir: Path = paths.data("raw")
    assert raw_dir.is_dir(), "data/raw/ directory was not created."

    # Verify write access by creating a temporary file.
    tmp_file = raw_dir / "tmp_test_write.txt"
    try:
        tmp_file.write_text("verification")
        assert tmp_file.read_text() == "verification"
    finally:
        if tmp_file.exists():
            tmp_file.unlink()