"""
Unit tests for the data loaders in code/utils/loaders.py.

These tests verify that the loaders:
1. Correctly load existing real data.
2. Raise appropriate errors when data is missing (fail loudly).
"""
import json
import pytest
from pathlib import Path
import tempfile
import os

from code.utils.loaders import load_cot_traces

def test_load_cot_traces_success():
    """Test loading a valid CoT traces file."""
    # Create a temporary file with valid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([{"task_id": "1", "trace": "test"}], f)
        temp_path = f.name

    try:
        traces = load_cot_traces(temp_path)
        assert isinstance(traces, list)
        assert len(traces) == 1
        assert traces[0]["task_id"] == "1"
    finally:
        os.unlink(temp_path)

def test_load_cot_traces_missing_file():
    """Test that load_cot_traces raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        load_cot_traces("data/raw/nonexistent_traces.json")

def test_load_cot_traces_invalid_json():
    """Test that load_cot_traces raises error for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("not valid json")
        temp_path = f.name

    try:
        with pytest.raises(json.JSONDecodeError):
            load_cot_traces(temp_path)
    finally:
        os.unlink(temp_path)
