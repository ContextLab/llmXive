"""
Integration tests for the Quickstart Validation script.

These tests ensure that the validation script correctly identifies
missing files, valid outputs, and handles execution errors.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from validate_quickstart import (
    check_file_exists,
    validate_json_content,
    validate_yaml_content,
    verify_outputs,
    main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)

def test_check_file_exists_found(temp_dir):
    """Test that check_file_exists returns True for existing file."""
    test_file = temp_dir / "test.txt"
    test_file.touch()
    assert check_file_exists(test_file, "Test File") is True

def test_check_file_exists_missing(temp_dir):
    """Test that check_file_exists returns False for missing file."""
    missing_file = temp_dir / "missing.txt"
    assert check_file_exists(missing_file, "Missing File") is False

def test_validate_json_content_valid(temp_dir):
    """Test validation of valid JSON content."""
    test_file = temp_dir / "valid.json"
    test_file.write_text('{"key": "value"}')
    assert validate_json_content(test_file) is True

def test_validate_json_content_invalid(temp_dir):
    """Test validation of invalid JSON content."""
    test_file = temp_dir / "invalid.json"
    test_file.write_text('{invalid json}')
    assert validate_json_content(test_file) is False

def test_validate_yaml_content_valid(temp_dir):
    """Test validation of valid YAML content."""
    test_file = temp_dir / "valid.yaml"
    test_file.write_text('key: value\nlist:\n  - item1')
    assert validate_yaml_content(test_file) is True

def test_validate_yaml_content_invalid(temp_dir):
    """Test validation of invalid YAML content."""
    test_file = temp_dir / "invalid.yaml"
    test_file.write_text('key: [unclosed')
    assert validate_yaml_content(test_file) is False

def test_verify_outputs_all_present(temp_dir):
    """Test verify_outputs when all expected files are present."""
    # Create mock output structure
    (temp_dir / "results").mkdir()
    (temp_dir / "results" / "model_metrics.json").write_text('{"r2": 0.5}')
    (temp_dir / "results" / "channel_importance.json").write_text('{"ch1": 0.1}')
    (temp_dir / "results" / "sensitivity_report.csv").write_text('window,r2\n1,0.5\n2,0.6')

    # Mock EXPECTED_OUTPUTS for this test context
    import validate_quickstart
    original_expected = validate_quickstart.EXPECTED_OUTPUTS
    validate_quickstart.EXPECTED_OUTPUTS = [
        "results/model_metrics.json",
        "results/channel_importance.json",
        "results/sensitivity_report.csv"
    ]

    try:
        result = verify_outputs(temp_dir)
        assert result is True
    finally:
        validate_quickstart.EXPECTED_OUTPUTS = original_expected

def test_verify_outputs_missing_file(temp_dir):
    """Test verify_outputs when an expected file is missing."""
    (temp_dir / "results").mkdir()
    (temp_dir / "results" / "model_metrics.json").write_text('{"r2": 0.5}')
    # Missing channel_importance.json and sensitivity_report.csv

    import validate_quickstart
    original_expected = validate_quickstart.EXPECTED_OUTPUTS
    validate_quickstart.EXPECTED_OUTPUTS = [
        "results/model_metrics.json",
        "results/channel_importance.json",
        "results/sensitivity_report.csv"
    ]

    try:
        result = verify_outputs(temp_dir)
        assert result is False
    finally:
        validate_quickstart.EXPECTED_OUTPUTS = original_expected
