"""
Unit tests for the parser module (T006a).
"""
import pytest
import pandas as pd
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from parser import (
    extract_metrics_from_trajectory,
    validate_trajectory_against_schema,
    parse_trajectories,
    compute_file_checksum,
    load_schema
)

@pytest.fixture
def sample_schema():
    return {
        "type": "object",
        "required": ["trajectory_id", "turn", "legal_moves"],
        "properties": {
            "trajectory_id": {"type": "string"},
            "turn": {"type": "integer"},
            "legal_moves": {"type": "array", "items": {"type": "string"}}
        }
    }

@pytest.fixture
def valid_trajectory():
    return {
        "trajectory_id": "test_001",
        "turn": 1,
        "legal_moves": ["move_a", "move_b"]
    }

def test_extract_metrics_from_trajectory(valid_trajectory):
    """Test extraction of metrics from a valid trajectory."""
    metrics = extract_metrics_from_trajectory(valid_trajectory)
    assert metrics["trajectory_id"] == "test_001"
    assert metrics["turn"] == 1
    assert metrics["legal_moves"] == ["move_a", "move_b"]
    assert metrics["num_legal_moves"] == 2

def test_extract_metrics_missing_fields():
    """Test extraction with missing optional fields."""
    trajectory = {
        "trajectory_id": "test_002",
        "turn": 2
    }
    metrics = extract_metrics_from_trajectory(trajectory)
    assert metrics["trajectory_id"] == "test_002"
    assert metrics["turn"] == 2
    assert metrics["legal_moves"] == []
    assert metrics["num_legal_moves"] == 0

def test_validate_trajectory_against_schema_valid(sample_schema, valid_trajectory):
    """Test validation of a valid trajectory."""
    assert validate_trajectory_against_schema(valid_trajectory, sample_schema) is True

def test_validate_trajectory_against_schema_missing_required(sample_schema):
    """Test validation with missing required field."""
    trajectory = {
        "trajectory_id": "test_003",
        "turn": 3
        # Missing legal_moves
    }
    assert validate_trajectory_against_schema(trajectory, sample_schema) is False

def test_validate_trajectory_against_schema_wrong_type(sample_schema):
    """Test validation with wrong type."""
    trajectory = {
        "trajectory_id": 123,  # Should be string
        "turn": 1,
        "legal_moves": ["move_a"]
    }
    assert validate_trajectory_against_schema(trajectory, sample_schema) is False

def test_compute_file_checksum(tmp_path):
    """Test checksum computation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    checksum = compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_load_schema(tmp_path):
    """Test schema loading."""
    schema_file = tmp_path / "schema.yaml"
    schema_content = """
    type: object
    required:
      - field1
    properties:
      field1:
        type: string
    """
    schema_file.write_text(schema_content)
    
    with patch('parser.SCHEMA_PATH', schema_file):
        schema = load_schema()
        assert schema["type"] == "object"
        assert "field1" in schema["required"]
