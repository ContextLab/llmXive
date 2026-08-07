import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from validation.final_validator import (
    load_json_file,
    check_stability_rankings,
    check_runtime,
    check_manifest,
    run_final_validation
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_json_file_exists(temp_dir):
    """Test loading an existing JSON file."""
    test_file = temp_dir / "test.json"
    test_data = {"key": "value"}
    with open(test_file, 'w') as f:
        json.dump(test_data, f)

    result = load_json_file(test_file)
    assert result == test_data

def test_load_json_file_missing(temp_dir):
    """Test loading a missing JSON file returns None."""
    missing_file = temp_dir / "missing.json"
    result = load_json_file(missing_file)
    assert result is None

def test_load_json_file_invalid(temp_dir):
    """Test loading an invalid JSON file returns None."""
    invalid_file = temp_dir / "invalid.json"
    with open(invalid_file, 'w') as f:
        f.write("{ invalid json }")

    result = load_json_file(invalid_file)
    assert result is None

def test_check_stability_rankings_valid(temp_dir):
    """Test stability rankings check with valid data."""
    test_file = temp_dir / "stability_rankings.json"
    test_data = {
        "runs": [
            {"top_features": ["A", "B", "C"]},
            {"top_features": ["A", "B", "C"]},
            {"top_features": ["A", "B", "C"]}
        ]
    }
    with open(test_file, 'w') as f:
        json.dump(test_data, f)

    result = check_stability_rankings(test_file)
    assert result["file_exists"] is True
    assert result["valid_schema"] is True
    assert result["criterion_met"] is True

def test_check_stability_rankings_missing(temp_dir):
    """Test stability rankings check with missing file."""
    missing_file = temp_dir / "missing.json"
    result = check_stability_rankings(missing_file)
    assert result["file_exists"] is False
    assert result["criterion_met"] is False

def test_check_runtime_valid(temp_dir):
    """Test runtime check with valid data."""
    test_file = temp_dir / "pipeline_runtime.json"
    test_data = {
        "total_runtime_seconds": 3600.0,
        "limit_seconds": 7200,
        "status": "pass"
    }
    with open(test_file, 'w') as f:
        json.dump(test_data, f)

    result = check_runtime(test_file)
    assert result["file_exists"] is True
    assert result["valid_schema"] is True
    assert result["status"] == "pass"

def test_check_runtime_fail(temp_dir):
    """Test runtime check with failed status."""
    test_file = temp_dir / "pipeline_runtime.json"
    test_data = {
        "total_runtime_seconds": 8000.0,
        "limit_seconds": 7200,
        "status": "fail"
    }
    with open(test_file, 'w') as f:
        json.dump(test_data, f)

    result = check_runtime(test_file)
    assert result["status"] == "fail"

def test_check_manifest_valid(temp_dir):
    """Test manifest check with valid data."""
    test_file = temp_dir / "manifest.json"
    test_data = {
        "seeds": 42,
        "hyperparameters": {},
        "versions": {},
        "timestamps": {},
        "checksums": {}
    }
    with open(test_file, 'w') as f:
        json.dump(test_data, f)

    result = check_manifest(test_file)
    assert result["file_exists"] is True
    assert result["valid_schema"] is True

def test_check_manifest_missing_fields(temp_dir):
    """Test manifest check with missing fields."""
    test_file = temp_dir / "manifest.json"
    test_data = {
        "seeds": 42,
        "hyperparameters": {}
    }
    with open(test_file, 'w') as f:
        json.dump(test_data, f)

    result = check_manifest(test_file)
    assert result["valid_schema"] is False
    assert "Missing fields" in result["details"]
