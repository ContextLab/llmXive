"""
Unit tests for the Independence Validator (T039).
"""
import json
import csv
import tempfile
import pytest
from pathlib import Path

from src.services.independence_validator import (
    load_trajectory_ids,
    load_kappa_trajectory_ids,
    validate_independence,
    FatalError,
    setup_logger
)

@pytest.fixture
def logger():
    return setup_logger("test_independence_validator")

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_load_trajectory_ids_list_format(temp_dir):
    """Test loading IDs from a simple list format."""
    file_path = temp_dir / "trajectory_ids.json"
    data = ["id_1", "id_2", "id_3"]
    with open(file_path, "w") as f:
        json.dump(data, f)
    
    ids = load_trajectory_ids(file_path)
    assert ids == {"id_1", "id_2", "id_3"}

def test_load_trajectory_ids_dict_format(temp_dir):
    """Test loading IDs from a dict with 'trajectories' key."""
    file_path = temp_dir / "trajectory_ids.json"
    data = {
        "trajectories": [
            {"id": "id_1", "meta": "data1"},
            {"id": "id_2", "meta": "data2"}
        ]
    }
    with open(file_path, "w") as f:
        json.dump(data, f)
    
    ids = load_trajectory_ids(file_path)
    assert ids == {"id_1", "id_2"}

def test_load_trajectory_ids_file_not_found(temp_dir):
    """Test that FileNotFoundError is raised if file is missing."""
    file_path = temp_dir / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        load_trajectory_ids(file_path)

def test_load_kappa_ids_valid(temp_dir):
    """Test loading IDs from a valid kappa CSV."""
    file_path = temp_dir / "kappa.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["system_size", "kappa", "trajectory_id"])
        writer.writeheader()
        writer.writerow({"system_size": 1000, "kappa": 1.2, "trajectory_id": "tid_1"})
        writer.writerow({"system_size": 2000, "kappa": 1.5, "trajectory_id": "tid_2"})
    
    ids = load_kappa_trajectory_ids(file_path)
    assert ids == {"tid_1", "tid_2"}

def test_load_kappa_ids_missing_column(temp_dir):
    """Test that KeyError is raised if 'trajectory_id' is missing."""
    file_path = temp_dir / "kappa.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["system_size", "kappa"])
        writer.writeheader()
        writer.writerow({"system_size": 1000, "kappa": 1.2})
    
    with pytest.raises(KeyError):
        load_kappa_trajectory_ids(file_path)

def test_validate_independence_success(logger):
    """Test that validation passes when sets are disjoint."""
    meta_ids = {"meta_1", "meta_2"}
    kappa_ids = {"kappa_1", "kappa_2"}
    
    # Should not raise
    result = validate_independence(meta_ids, kappa_ids, logger)
    assert result is True

def test_validate_independence_failure(logger):
    """Test that FatalError is raised when sets overlap."""
    meta_ids = {"meta_1", "overlap_id"}
    kappa_ids = {"kappa_1", "overlap_id"}
    
    with pytest.raises(FatalError) as exc_info:
        validate_independence(meta_ids, kappa_ids, logger)
    
    assert "NOT independent" in str(exc_info.value)
    assert "overlap_id" in str(exc_info.value)

def test_validate_independence_empty_sets(logger):
    """Test behavior with empty sets (should pass as no overlap, though logically suspect)."""
    # Technically disjoint, but might be a logical error in upstream.
    # The validator only checks intersection.
    meta_ids = set()
    kappa_ids = set()
    
    result = validate_independence(meta_ids, kappa_ids, logger)
    assert result is True