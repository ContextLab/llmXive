"""Unit tests for the data_fetcher utilities."""

import json
import tempfile
from pathlib import Path

import pytest

from utils.data_fetcher import (
    calculate_checksum,
    fetch_dataset,
    DataFetchError,
    _generate_synthetic_graph,
)


def test_calculate_checksum(tmp_path: Path):
    """Checksum of a known file should match the expected value."""
    content = b"llmxive test"
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(content)

    expected = "dbef2c0b9bdc7f2d5d5c8c2c2d8c8c4c7f3c4f5d6e7a8b9c0d1e2f3a4b5c6d7"
    # The exact hash value depends on the algorithm; compute it dynamically for the test
    import hashlib

    digest = hashlib.sha256(content).hexdigest()
    assert calculate_checksum(file_path) == digest


def test_fetch_dataset_synthetic_fallback(tmp_path: Path):
    """When a non‑existent dataset is requested, synthetic fallback should create a file."""
    bogus_name = "nonexistent/dataset"
    dest = tmp_path / "synthetic.jsonl"

    path = fetch_dataset(
        name=bogus_name,
        split="train",
        dest_path=dest,
        allow_synthetic=True,
    )
    assert path == dest
    assert path.is_file()

    # Verify that the file contains the synthetic flag
    lines = path.read_text().strip().splitlines()
    assert len(lines) > 0
    first_record = json.loads(lines[0])
    assert first_record.get("synthetic_flag") == 1


def test_fetch_dataset_real_failure_without_synthetic():
    """Fetching a bad dataset without synthetic flag must raise."""
    with pytest.raises(DataFetchError):
        fetch_dataset(
            name="nonexistent/dataset",
            split="train",
            dest_path=None,
            allow_synthetic=False,
        )