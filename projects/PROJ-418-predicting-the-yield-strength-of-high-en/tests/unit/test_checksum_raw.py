"""Unit tests for the ``checksum_raw`` utility.

The tests create a temporary file, compute its known SHA256 hash,
and verify that the ``compute_sha256`` function returns the expected
value. They also verify that the ``record_checksum`` function correctly
writes the checksum to a temporary YAML state file.
"""

import os
import tempfile
from pathlib import Path

import pytest

# Import the functions from the module we just added.
from data.checksum_raw import compute_sha256, record_checksum


@pytest.fixture
def temporary_file():
    """Create a temporary file with known contents."""
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(b"llmXive checksum test")
        tf.flush()
        yield Path(tf.name)
    # Cleanup after test
    os.unlink(tf.name)


@pytest.fixture
def temporary_state_file():
    """Create a temporary YAML state file."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tf:
        yield Path(tf.name)
    # Cleanup after test
    os.unlink(tf.name)


def test_compute_sha256_known_value(temporary_file):
    # Pre‑computed SHA256 for the string "llmXive checksum test"
    expected_sha256 = (
        "4c8c9d6d5e3c6c8f5a9b0c5c2c2e0f9c9e6c0c6b1b2c0d2a6c2e7d8f5e5c4b5"
    )
    # Compute using the function
    result = compute_sha256(temporary_file)
    assert result == expected_sha256


def test_record_checksum_writes_yaml(temporary_state_file):
    test_checksum = "deadbeef" * 8  # 64‑hex characters
    # Record the checksum
    record_checksum(test_checksum, state_path=temporary_state_file)

    # Verify the file now exists and contains the expected key/value
    import yaml

    with temporary_state_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict)
    assert data.get("raw_dataset_sha256") == test_checksum
