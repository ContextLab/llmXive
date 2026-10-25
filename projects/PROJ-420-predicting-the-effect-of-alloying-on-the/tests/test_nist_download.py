"""
Tests for the NIST MDR download implementation (T009b).
Ensures that the function fetch_nist_data returns a non‑empty list and
writes the expected JSON file to ``data/raw/nist_alloys.json``.
"""
import json
from pathlib import Path

import pytest

from code.data._download_logic import fetch_nist_data, _ensure_output_dir

@pytest.fixture
def temp_output_dir(tmp_path):
    # Provide a temporary directory for the JSON output
    return tmp_path

def test_fetch_nist_data_success(temp_output_dir):
    records = fetch_nist_data(output_dir=Path(temp_output_dir))
    # Verify we got a list of dicts
    assert isinstance(records, list)
    assert all(isinstance(r, dict) for r in records)
    # Verify file was written
    out_path = Path(temp_output_dir) / "nist_alloys.json"
    assert out_path.is_file()
    # Load the file and compare contents
    with open(out_path, "r", encoding="utf-8") as f:
        file_records = json.load(f)
    assert file_records == records

def test_ensure_output_dir_creates_path():
    # Use a fresh temporary subdirectory
    temp_dir = Path("data") / "raw" / "test_subdir"
    if temp_dir.exists():
        # Ensure a clean state
        for child in temp_dir.iterdir():
            child.unlink()
        temp_dir.rmdir()
    result = _ensure_output_dir(temp_dir)
    assert result == temp_dir
    assert result.is_dir()