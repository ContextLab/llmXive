"""
Unit tests for code/baseline_ref.py
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
# We assume the test runs from the project root or tests/ is in PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.baseline_ref import (
    load_baseline_saa,
    get_baseline_value,
    validate_baseline_consistency,
    BaselineSchemaError,
    get_baseline_path
)


@pytest.fixture
def valid_baseline_json():
    return {
        "baseline_saa": 0.68,
        "source": "CiteVQA Paper (Chen et al., 2024), Table 3: Human Baseline SAA"
    }


@pytest.fixture
def temp_baseline_file(valid_baseline_json):
    """Creates a temporary file with valid baseline JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_baseline_json, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_load_baseline_saa_success(temp_baseline_file, valid_baseline_json):
    """Test successful loading of baseline data."""
    with patch('code.baseline_ref.get_baseline_path', return_value=Path(temp_baseline_file)):
        result = load_baseline_saa()
        assert result["baseline_saa"] == valid_baseline_json["baseline_saa"]
        assert result["source"] == valid_baseline_json["source"]


def test_get_baseline_value_success(temp_baseline_file):
    """Test retrieving just the scalar value."""
    with patch('code.baseline_ref.get_baseline_path', return_value=Path(temp_baseline_file)):
        value = get_baseline_value()
        assert value == 0.68
        assert isinstance(value, float)


def test_load_baseline_missing_file():
    """Test error handling when file does not exist."""
    fake_path = Path("/non/existent/path.json")
    with patch('code.baseline_ref.get_baseline_path', return_value=fake_path):
        with pytest.raises(FileNotFoundError):
            load_baseline_saa()


def test_load_baseline_invalid_json(tmp_path):
    """Test error handling for malformed JSON."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ invalid json }")
    
    with patch('code.baseline_ref.get_baseline_path', return_value=bad_file):
        with pytest.raises(json.JSONDecodeError):
            load_baseline_saa()


def test_load_baseline_missing_keys(tmp_path):
    """Test error handling for missing schema keys."""
    bad_file = tmp_path / "bad_schema.json"
    bad_file.write_text(json.dumps({"baseline_saa": 0.68})) # Missing 'source'

    with patch('code.baseline_ref.get_baseline_path', return_value=bad_file):
        with pytest.raises(BaselineSchemaError) as exc_info:
            load_baseline_saa()
        assert "missing required keys" in str(exc_info.value)


def test_load_baseline_wrong_type(tmp_path):
    """Test error handling for wrong data types."""
    bad_file = tmp_path / "bad_type.json"
    bad_file.write_text(json.dumps({"baseline_saa": "not_a_number", "source": "test"}))

    with patch('code.baseline_ref.get_baseline_path', return_value=bad_file):
        with pytest.raises(BaselineSchemaError) as exc_info:
            load_baseline_saa()
        assert "must be a number" in str(exc_info.value)


def test_validate_baseline_consistency_true(temp_baseline_file):
    """Test consistency check when values match within tolerance."""
    with patch('code.baseline_ref.get_baseline_path', return_value=Path(temp_baseline_file)):
        # 0.68 vs 0.6805 (diff 0.0005 < 0.001)
        assert validate_baseline_consistency(0.6805, tolerance=0.001) is True


def test_validate_baseline_consistency_false(temp_baseline_file):
    """Test consistency check when values differ significantly."""
    with patch('code.baseline_ref.get_baseline_path', return_value=Path(temp_baseline_file)):
        # 0.68 vs 0.70 (diff 0.02 > 0.001)
        assert validate_baseline_consistency(0.70, tolerance=0.001) is False