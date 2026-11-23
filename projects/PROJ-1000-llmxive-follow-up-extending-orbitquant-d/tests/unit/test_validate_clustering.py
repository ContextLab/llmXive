"""
Unit tests for code/validation/validate_clustering.py (T023a).
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validation.validate_clustering import (
    validate_structure,
    validate_data_types,
    validate_consistency,
    REQUIRED_TOP_LEVEL_KEYS
)

def create_temp_report(data):
    """Helper to create a temporary JSON file."""
    fd, path = tempfile.mkdtemp()
    file_path = os.path.join(fd, "test_report.json")
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return Path(file_path), fd

def teardown_temp(path, fd):
    """Helper to remove temporary directory."""
    import shutil
    shutil.rmtree(fd)

@pytest.fixture
def valid_report_data():
    """Fixture providing a valid clustering report structure."""
    return {
        "layers": ["layer1", "layer2"],
        "subsets": [{"subset_id": 0}, {"subset_id": 1}],
        "boundaries": [0.5, 1.0],
        "matrices": {
            "layer1": {
                "shape": [4, 4],
                "data": [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
            },
            "layer2": {
                "shape": [4, 4],
                "data": [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
            }
        }
    }

@pytest.fixture
def missing_keys_report_data():
    """Fixture providing a report with missing required keys."""
    return {
        "layers": ["layer1"],
        "subsets": []
        # Missing 'boundaries' and 'matrices'
    }

@pytest.fixture
def invalid_matrix_data():
    """Fixture providing a report with non-numeric matrix data."""
    return {
        "layers": ["layer1"],
        "subsets": [{"subset_id": 0}],
        "boundaries": [0.5],
        "matrices": {
            "layer1": {
                "shape": [2, 2],
                "data": [["a", "b"], ["c", "d"]]  # Non-numeric
            }
        }
    }

@pytest.fixture
def non_list_subsets():
    """Fixture providing a report with non-list subsets."""
    return {
        "layers": ["layer1"],
        "subsets": {"key": "value"},  # Should be list
        "boundaries": [0.5],
        "matrices": {
            "layer1": {
                "shape": [2, 2],
                "data": [[1.0, 0.0], [0.0, 1.0]]
            }
        }
    }

def test_validate_structure_valid(valid_report_data):
    """Test validation passes on valid data."""
    report_path, fd = create_temp_report(valid_report_data)
    try:
        is_valid, errors = validate_structure(report_path)
        assert is_valid is True
        assert len(errors) == 0
    finally:
        teardown_temp(report_path, fd)

def test_validate_structure_missing_keys(missing_keys_report_data):
    """Test validation fails when required keys are missing."""
    report_path, fd = create_temp_report(missing_keys_report_data)
    try:
        is_valid, errors = validate_structure(report_path)
        assert is_valid is False
        assert any("Missing required top-level keys" in err for err in errors)
    finally:
        teardown_temp(report_path, fd)

def test_validate_structure_file_not_found():
    """Test validation fails when file does not exist."""
    fake_path = Path("/tmp/does_not_exist_12345.json")
    is_valid, errors = validate_structure(fake_path)
    assert is_valid is False
    assert any("File not found" in err for err in errors)

def test_validate_data_types_valid(valid_report_data):
    """Test data type validation passes on valid data."""
    report_path, fd = create_temp_report(valid_report_data)
    try:
        is_valid, errors = validate_data_types(report_path)
        assert is_valid is True
        assert len(errors) == 0
    finally:
        teardown_temp(report_path, fd)

def test_validate_data_types_invalid_matrix(invalid_matrix_data):
    """Test data type validation fails on non-numeric matrix data."""
    report_path, fd = create_temp_report(invalid_matrix_data)
    try:
        is_valid, errors = validate_data_types(report_path)
        assert is_valid is False
        assert any("non-numeric" in err for err in errors)
    finally:
        teardown_temp(report_path, fd)

def test_validate_data_types_non_list_subsets(non_list_subsets):
    """Test data type validation fails on non-list subsets."""
    report_path, fd = create_temp_report(non_list_subsets)
    try:
        is_valid, errors = validate_data_types(report_path)
        assert is_valid is False
        assert any("'subsets' field must be a list" in err for err in errors)
    finally:
        teardown_temp(report_path, fd)

def test_validate_consistency_valid(valid_report_data):
    """Test consistency validation passes on valid data."""
    report_path, fd = create_temp_report(valid_report_data)
    try:
        is_valid, errors = validate_consistency(report_path)
        assert is_valid is True
        assert len(errors) == 0
    finally:
        teardown_temp(report_path, fd)

def test_validate_consistency_empty_matrices():
    """Test consistency validation fails if no matrices are present."""
    data = {
        "layers": ["layer1"],
        "subsets": [{"subset_id": 0}],
        "boundaries": [0.5],
        "matrices": {}  # Empty
    }
    report_path, fd = create_temp_report(data)
    try:
        is_valid, errors = validate_consistency(report_path)
        assert is_valid is False
        assert any("No rotation matrices found" in err for err in errors)
    finally:
        teardown_temp(report_path, fd)