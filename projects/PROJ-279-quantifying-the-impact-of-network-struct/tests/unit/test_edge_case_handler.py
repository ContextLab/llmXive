"""
Unit tests for the edge case handler (T017).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from code.edge_case_handler import (
    detect_corruption,
    validate_coordination_numbers,
    handle_edge_cases,
    CorruptedFileError,
    UnexpectedCoordinationError,
    save_edge_case_report
)
from code.models.atomic_config import AtomicConfiguration


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def valid_config():
    """Creates a valid AtomicConfiguration with expected coordination numbers."""
    # 4 atoms, each connected to 2 others (coordination 2) - within bounds (2-6)
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 1.0, 0.0]
    ])
    # Neighbors: 0->1, 1->0,2, 2->1,3, 3->2 (simple chain/cycle)
    # Coordination: 1, 2, 2, 1 (all within 2-6? No, 1 is < 2. Let's adjust.)
    # Let's make a 4-cycle: 0-1, 1-2, 2-3, 3-0. All coord = 2.
    neighbors = [
        [1, 3], # 0 connected to 1 and 3
        [0, 2], # 1 connected to 0 and 2
        [1, 3], # 2 connected to 1 and 3
        [0, 2]  # 3 connected to 0 and 2
    ]
    config = AtomicConfiguration(
        id="valid_config_001",
        atomic_numbers=[14, 14, 14, 14], # Si
        coordinates=coords,
        neighbors=neighbors,
        file_path="dummy.xyz"
    )
    return config


@pytest.fixture
def invalid_config():
    """Creates an AtomicConfiguration with unexpected coordination numbers."""
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0]
    ])
    # Neighbors: 0->1 (coord 1), 1->0,2 (coord 2), 2->1 (coord 1)
    # Coordination 1 is < MIN_EXPECTED_COORD (2) -> Invalid
    neighbors = [
        [1],
        [0, 2],
        [1]
    ]
    config = AtomicConfiguration(
        id="invalid_config_001",
        atomic_numbers=[14, 14, 14],
        coordinates=coords,
        neighbors=neighbors,
        file_path="dummy.xyz"
    )
    return config


def test_detect_corruption_missing_file(temp_dir):
    """Test detection of missing file."""
    result = detect_corruption(temp_dir / "nonexistent.xyz")
    assert result is True


def test_detect_corruption_empty_file(temp_dir):
    """Test detection of empty file."""
    file_path = temp_dir / "empty.xyz"
    file_path.touch()
    result = detect_corruption(file_path)
    assert result is True


def test_detect_corruption_valid_json(temp_dir):
    """Test detection of valid JSON file."""
    file_path = temp_dir / "valid.json"
    with open(file_path, 'w') as f:
        json.dump({"key": "value"}, f)
    result = detect_corruption(file_path)
    assert result is False


def test_detect_corruption_invalid_json(temp_dir):
    """Test detection of invalid JSON file."""
    file_path = temp_dir / "invalid.json"
    with open(file_path, 'w') as f:
        f.write("{ invalid json }")
    result = detect_corruption(file_path)
    assert result is True


def test_validate_coordination_numbers_valid(valid_config):
    """Test validation of a configuration with valid coordination numbers."""
    is_valid, unexpected = validate_coordination_numbers(valid_config)
    assert is_valid is True
    assert unexpected == []


def test_validate_coordination_numbers_invalid(invalid_config):
    """Test validation of a configuration with invalid coordination numbers."""
    is_valid, unexpected = validate_coordination_numbers(invalid_config)
    assert is_valid is False
    assert 1 in unexpected


def test_handle_edge_cases_corrupted_file_raises(temp_dir):
    """Test that handle_edge_cases raises CorruptedFileError on corrupted file."""
    # Create a corrupted file
    corrupted_path = temp_dir / "corrupted.xyz"
    with open(corrupted_path, 'w') as f:
        f.write("not a valid xyz") # Will fail XYZ check if we add strict XYZ parsing, but let's use JSON for clarity
    # Let's use a JSON file that is corrupted
    corrupted_json = temp_dir / "corrupted.json"
    with open(corrupted_json, 'w') as f:
        f.write("{ broken }")

    config = AtomicConfiguration(
        id="bad_file",
        atomic_numbers=[14],
        coordinates=np.array([[0,0,0]]),
        neighbors=[[]],
        file_path=str(corrupted_json)
    )

    with pytest.raises(CorruptedFileError):
        handle_edge_cases([config], strict_mode=True)


def test_handle_edge_cases_strict_mode_drops_invalid(valid_config, invalid_config):
    """Test that strict mode drops configurations with invalid coordination."""
    report = handle_edge_cases([valid_config, invalid_config], strict_mode=True)

    assert len(report["processed"]) == 1
    assert report["processed"][0].id == "valid_config_001"
    assert len(report["dropped"]) == 1
    assert report["dropped"][0]["id"] == "invalid_config_001"
    assert len(report["flagged"]) == 0


def test_handle_edge_cases_non_strict_mode_flags_invalid(valid_config, invalid_config):
    """Test that non-strict mode flags configurations with invalid coordination."""
    report = handle_edge_cases([valid_config, invalid_config], strict_mode=False)

    assert len(report["processed"]) == 1
    assert report["processed"][0].id == "valid_config_001"
    assert len(report["flagged"]) == 1
    assert report["flagged"][0]["id"] == "invalid_config_001"
    assert len(report["dropped"]) == 0


def test_save_edge_case_report(temp_dir):
    """Test saving the edge case report."""
    report = {
        "summary": {"total_input": 2, "processed": 1, "flagged": 0, "dropped": 1, "errors": 0},
        "flagged": [],
        "dropped": [{"id": "bad", "reason": "coord", "details": [1]}],
        "errors": []
    }
    output_path = temp_dir / "report.json"
    result_path = save_edge_case_report(report, output_path)

    assert result_path == output_path
    assert output_path.exists()

    with open(output_path, 'r') as f:
        data = json.load(f)

    assert data["summary"]["dropped"] == 1
    assert len(data["dropped"]) == 1