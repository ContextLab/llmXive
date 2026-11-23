import json
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.modeling.verify_success_criterion import (
    load_json_file,
    calculate_lift,
    verify_success_criterion
)
from code.config import get_path_validation, ensure_directory

def test_calculate_lift():
    """Test the calculate_lift function."""
    assert calculate_lift(0.85, 0.60) == 0.25
    assert calculate_lift(0.50, 0.50) == 0.0
    assert calculate_lift(0.40, 0.60) == -0.20

def test_verify_success_criterion_passed():
    """Test verification when the criterion is met."""
    result = verify_success_criterion(
        actual_accuracy=0.85,
        baseline_accuracy=0.60,
        lift_threshold=0.10
    )
    assert result['status'] == 'passed'
    assert result['lift_value'] == 0.25
    assert result['is_deferred'] is False
    assert 'MET' in result['message']

def test_verify_success_criterion_failed():
    """Test verification when the criterion is not met."""
    result = verify_success_criterion(
        actual_accuracy=0.65,
        baseline_accuracy=0.60,
        lift_threshold=0.10
    )
    assert result['status'] == 'failed'
    assert result['lift_value'] == 0.05
    assert result['is_deferred'] is False
    assert 'NOT MET' in result['message']

def test_verify_success_criterion_deferred():
    """Test verification when the threshold is deferred."""
    result = verify_success_criterion(
        actual_accuracy=0.85,
        baseline_accuracy=0.60,
        lift_threshold=0.0,
        is_deferred=True
    )
    assert result['status'] == 'deferred'
    assert result['is_deferred'] is True
    assert 'DEFERRED' in result['message']

def test_load_json_file_not_found():
    """Test that load_json_file raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        load_json_file(Path("/nonexistent/path/file.json"))

@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    file_path = tmp_path / "test.json"
    data = {"key": "value"}
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def test_load_json_file_success(temp_json_file):
    """Test successful loading of a JSON file."""
    data = load_json_file(temp_json_file)
    assert data == {"key": "value"}