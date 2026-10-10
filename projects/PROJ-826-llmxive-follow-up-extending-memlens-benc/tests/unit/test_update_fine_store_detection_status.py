"""
Unit tests for ``code/update_fine_store_detection_status.py``.
The tests verify that the merging logic correctly adds a ``detection_status``
field for every fine‑store entry, handling all three possible statuses and
falling back to ``fallback`` when a sample is missing from the detection
results.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import the functions directly from the module under test
from code.update_fine_store_detection_status import (
    merge_detection_status,
    load_json,
    write_json,
)

@pytest.fixture
def sample_fine_store(tmp_path: Path):
    """Create a temporary fine‑store JSON file."""
    data = [
        {"sample_id": "s1", "content": "entry 1"},
        {"sample_id": "s2", "content": "entry 2"},
        {"sample_id": "s3", "content": "entry 3"},
    ]
    file_path = tmp_path / "fine_store.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def sample_detection_results(tmp_path: Path):
    """Create a temporary detection results JSON file."""
    data = [
        {"sample_id": "s1", "detection_status": "success"},
        {"sample_id": "s2", "detection_status": "zero_detection"},
        # Note: s3 is intentionally omitted to test the fallback case
    ]
    file_path = tmp_path / "detection_results.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return file_path

def test_merge_detection_status_complete(sample_fine_store, sample_detection_results):
    fine_store = load_json(sample_fine_store)
    detection_results = load_json(sample_detection_results)

    merged = merge_detection_status(fine_store, detection_results)

    # Verify that each entry now has a detection_status field
    status_by_id = {e["sample_id"]: e["detection_status"] for e in merged}
    assert status_by_id["s1"] == "success"
    assert status_by_id["s2"] == "zero_detection"
    # s3 was missing from detection results → fallback
    assert status_by_id["s3"] == "fallback"

def test_write_and_load_roundtrip(tmp_path: Path):
    """Ensure that write_json/write_json round‑trip preserves data."""
    original = [
        {"sample_id": "a", "detection_status": "success"},
        {"sample_id": "b", "detection_status": "fallback"},
    ]
    file_path = tmp_path / "roundtrip.json"
    write_json(original, file_path)

    loaded = load_json(file_path)
    assert loaded == original

def test_missing_fine_store_raises(tmp_path: Path):
    missing_path = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        load_json(missing_path)

def test_invalid_json_structure(tmp_path: Path):
    # Write a dict instead of a list
    bad_path = tmp_path / "bad.json"
    with bad_path.open("w", encoding="utf-8") as f:
        json.dump({"not": "a list"}, f)
    with pytest.raises(ValueError):
        load_json(bad_path)