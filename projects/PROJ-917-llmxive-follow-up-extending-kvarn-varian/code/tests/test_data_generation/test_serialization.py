"""
Tests for data serialization (Parquet/JSON) with checksums.
"""
import pytest
from data_generation.utils import save_json_with_checksum
import json
import tempfile
from pathlib import Path

def test_serialization_round_trip(tmp_path):
    """Test saving and loading JSON with checksum."""
    data = {"step": 1, "value": 42.5}
    output_file = tmp_path / "data.json"
    save_json_with_checksum(data, output_file)
    
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == data
