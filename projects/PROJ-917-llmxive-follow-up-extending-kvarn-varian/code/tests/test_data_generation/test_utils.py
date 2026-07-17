"""
Additional tests for data generation utilities.
"""
import pytest
from data_generation.utils import compute_checksum, save_json_with_checksum
import json
import tempfile
from pathlib import Path

def test_compute_checksum():
    """Test checksum calculation."""
    data = {"key": "value"}
    checksum = compute_checksum(json.dumps(data))
    assert len(checksum) == 64  # SHA256 hex length

def test_save_json_with_checksum(tmp_path):
    """Test saving JSON with checksum file."""
    data = {"test": 123}
    output_file = tmp_path / "test.json"
    checksum_file = tmp_path / "test.json.sha256"
    save_json_with_checksum(data, output_file)
    assert output_file.exists()
    assert checksum_file.exists()
