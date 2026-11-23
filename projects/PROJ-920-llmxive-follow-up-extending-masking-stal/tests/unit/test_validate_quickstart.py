"""
Unit tests for the validate_quickstart module.

These tests verify the validation logic without executing the full pipeline.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validate_quickstart import (
    validate_file_exists,
    validate_json_structure,
    validate_trajectory_schema,
    validate_simulation_output
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

def test_validate_file_exists_exists(temp_dir):
    """Test that validate_file_exists returns True for existing file."""
    file_path = temp_dir / "test.txt"
    file_path.touch()
    assert validate_file_exists(file_path, "Test File") is True

def test_validate_file_exists_missing(temp_dir, caplog):
    """Test that validate_file_exists returns False for missing file."""
    file_path = temp_dir / "missing.txt"
    assert validate_file_exists(file_path, "Missing File") is False

def test_validate_json_structure_valid_list(temp_dir):
    """Test JSON validation with a list containing required keys."""
    file_path = temp_dir / "data.json"
    data = [{"key1": "val1", "key2": "val2"}]
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    assert validate_json_structure(file_path, ["key1", "key2"]) is True

def test_validate_json_structure_missing_key(temp_dir, caplog):
    """Test JSON validation fails when a key is missing."""
    file_path = temp_dir / "data.json"
    data = [{"key1": "val1"}]
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    assert validate_json_structure(file_path, ["key1", "key2"]) is False

def test_validate_trajectory_schema(temp_dir):
    """Test specific trajectory schema validation."""
    file_path = temp_dir / "traj.json"
    # Valid trajectory
    data = [{
        "evidence_turn_index": 5,
        "density_value": 0.75,
        "is_critical": True
    }]
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    assert validate_trajectory_schema(file_path) is True

def test_validate_trajectory_schema_invalid(temp_dir, caplog):
    """Test trajectory schema validation fails on missing fields."""
    file_path = temp_dir / "traj.json"
    data = [{"evidence_turn_index": 5}] # Missing density and is_critical
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    assert validate_trajectory_schema(file_path) is False

def test_validate_simulation_output_csv(temp_dir):
    """Test simulation output validation for CSV format."""
    file_path = temp_dir / "sim.csv"
    content = "horizon,density,success\n1,0.5,0\n2,0.8,1\n"
    with open(file_path, 'w') as f:
        f.write(content)
    
    assert validate_simulation_output(file_path) is True

def test_validate_simulation_output_csv_missing_cols(temp_dir, caplog):
    """Test simulation output validation fails if CSV missing columns."""
    file_path = temp_dir / "sim.csv"
    content = "horizon,density\n1,0.5\n" # Missing 'success'
    with open(file_path, 'w') as f:
        f.write(content)
    
    assert validate_simulation_output(file_path) is False

def test_validate_simulation_output_json(temp_dir):
    """Test simulation output validation for JSON format (fallback)."""
    file_path = temp_dir / "sim.json"
    data = [{"horizon": 1, "density": 0.5, "success": 0}]
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    assert validate_simulation_output(file_path) is True