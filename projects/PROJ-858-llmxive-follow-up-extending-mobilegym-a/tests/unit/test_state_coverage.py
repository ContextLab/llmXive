"""
Unit tests for the state_coverage module.

Tests binary vector initialization, transition detection, and aggregation.
"""

import json
import os
import sys
import tempfile
from typing import Dict, List

# Add parent directory to path for imports if running via pytest directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from code.scheduler.state_coverage import (
    initialize_coverage_vector,
    detect_transitions,
    aggregate_vectors,
    save_coverage_vector,
)
from code.utils.constants import get_coverage_schema

# Mock the schema for testing if the real one is not loaded correctly in isolation
# The module relies on constants.py which reads from contracts/coverage.schema.yaml
# We assume the schema is valid and contains standard keys.

def test_initialize_coverage_vector():
    """Test that the vector initializes with all zeros."""
    vector = initialize_coverage_vector()
    assert isinstance(vector, dict)
    # All values must be 0
    for k, v in vector.items():
        assert v == 0, f"Key {k} should be 0, got {v}"
    # Should not be empty
    assert len(vector) > 0

def test_detect_transitions_basic():
    """Test that detected states flip the correct bits to 1."""
    # Get a clean vector
    initial_vec = initialize_coverage_vector()
    keys = list(initial_vec.keys())
    target_key = keys[0] if keys else "dark_mode"

    # Create a mock log where the target key is present
    mock_log = {
        "states": [{"name": target_key, "value": True}]
    }

    result = detect_transitions(mock_log, initial_vec)

    assert result[target_key] == 1, f"State {target_key} should be 1"
    # Other states should remain 0
    for k in keys:
        if k != target_key:
            assert result[k] == 0

def test_detect_transitions_multiple():
    """Test detection of multiple states in one log."""
    initial_vec = initialize_coverage_vector()
    keys = list(initial_vec.keys())
    if len(keys) < 2:
        # Fallback if schema is too small
        keys = ["dark_mode", "wifi_connected"]

    mock_log = {
        "states": [
            {"name": keys[0], "value": True},
            {"name": keys[1], "value": True}
        ]
    }

    result = detect_transitions(mock_log, initial_vec)

    assert result[keys[0]] == 1
    assert result[keys[1]] == 1

def test_aggregate_vectors_union():
    """Test that aggregation performs a logical OR (union)."""
    vec1 = {"a": 1, "b": 0, "c": 0}
    vec2 = {"a": 0, "b": 1, "c": 0}
    vec3 = {"a": 0, "b": 0, "c": 1}

    result = aggregate_vectors([vec1, vec2, vec3])

    assert result["a"] == 1
    assert result["b"] == 1
    assert result["c"] == 1

def test_aggregate_vectors_empty():
    """Test aggregation of empty list returns zero vector."""
    result = aggregate_vectors([])
    # Should return a zero vector (initialized)
    for v in result.values():
        assert v == 0

def test_save_coverage_vector():
    """Test saving vector to file."""
    vector = {"test_key": 1, "test_key2": 0}
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_vec.json")
        save_coverage_vector(vector, path)

        assert os.path.exists(path)
        with open(path, "r") as f:
            loaded = json.load(f)

        assert loaded == vector