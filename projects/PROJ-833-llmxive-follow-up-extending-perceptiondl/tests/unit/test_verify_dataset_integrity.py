"""
Unit tests for code/analysis/verify_dataset_integrity.py
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.verify_dataset_integrity import (
    calculate_file_checksum,
    verify_schema_compliance,
    verify_checksums,
    run_integrity_check
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for testing."""
    file_path = temp_dir / "test.json"
    data = {
        "image_path": "test.jpg",
        "bounding_boxes": [
            {"x": 10, "y": 10, "w": 20, "h": 20, "id": 1},
            {"x": 50, "y": 50, "w": 20, "h": 20, "id": 2}
        ],
        "derived_relations": ["right of", "below"]
    }
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def sample_schema():
    """Create a sample JSON schema for testing."""
    return {
        "type": "object",
        "required": ["image_path", "bounding_boxes"],
        "properties": {
            "image_path": {"type": "string"},
            "bounding_boxes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["x", "y", "w", "h", "id"],
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "w": {"type": "integer"},
                        "h": {"type": "integer"},
                        "id": {"type": "integer"}
                    }
                }
            },
            "derived_relations": {"type": "array"}
        }
    }

def test_calculate_file_checksum(temp_dir):
    """Test checksum calculation."""
    file_path = temp_dir / "test.txt"
    content = b"Hello, World!"
    with open(file_path, 'wb') as f:
        f.write(content)

    checksum = calculate_file_checksum(file_path)
    expected = hashlib.sha256(content).hexdigest()

    assert checksum == expected
    assert len(checksum) == 64  # SHA-256 produces 64 hex characters

def test_calculate_file_checksum_nonexistent_file(temp_dir):
    """Test checksum calculation for non-existent file."""
    file_path = temp_dir / "nonexistent.txt"
    checksum = calculate_file_checksum(file_path)
    assert checksum == ""

def test_verify_schema_compliance_valid(sample_json_file, sample_schema):
    """Test schema validation with valid data."""
    is_compliant, msg = verify_schema_compliance(sample_json_file, sample_schema)
    assert is_compliant is True
    assert "compliant" in msg.lower()

def test_verify_schema_compliance_invalid(temp_dir, sample_schema):
    """Test schema validation with invalid data."""
    file_path = temp_dir / "invalid.json"
    data = {
        "image_path": 123,  # Should be string
        "bounding_boxes": "not an array"  # Should be array
    }
    with open(file_path, 'w') as f:
        json.dump(data, f)

    is_compliant, msg = verify_schema_compliance(file_path, sample_schema)
    assert is_compliant is False
    assert "error" in msg.lower() or "missing" in msg.lower()

def test_verify_schema_compliance_invalid_json(temp_dir, sample_schema):
    """Test schema validation with invalid JSON."""
    file_path = temp_dir / "invalid.json"
    with open(file_path, 'w') as f:
        f.write("not valid json {")

    is_compliant, msg = verify_schema_compliance(file_path, sample_schema)
    assert is_compliant is False
    assert "json" in msg.lower()

def test_verify_checksums(temp_dir):
    """Test checksum verification."""
    # Create test files
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")

    # Create checksums file
    checksums = {
        "file1.txt": hashlib.sha256(b"content1").hexdigest(),
        "file2.txt": hashlib.sha256(b"content2").hexdigest()
    }
    checksums_file = temp_dir / "checksums.json"
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f)

    valid, invalid = verify_checksums(temp_dir, checksums_file)
    assert valid == 2
    assert invalid == 0

def test_verify_checksums_mismatch(temp_dir):
    """Test checksum verification with mismatched checksums."""
    file1 = temp_dir / "file1.txt"
    file1.write_text("content1")

    # Create checksums file with wrong hash
    checksums = {
        "file1.txt": hashlib.sha256(b"wrong content").hexdigest()
    }
    checksums_file = temp_dir / "checksums.json"
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f)

    valid, invalid = verify_checksums(temp_dir, checksums_file)
    assert valid == 0
    assert invalid == 1

def test_verify_checksums_missing_file(temp_dir):
    """Test checksum verification with missing file."""
    # Create checksums file referencing non-existent file
    checksums = {
        "nonexistent.txt": "somehash"
    }
    checksums_file = temp_dir / "checksums.json"
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f)

    valid, invalid = verify_checksums(temp_dir, checksums_file)
    assert valid == 0
    assert invalid == 1

@patch('analysis.verify_dataset_integrity.load_schema_file')
@patch('analysis.verify_dataset_integrity.verify_schema_compliance')
@patch('analysis.verify_dataset_integrity.validate_no_overlaps')
def test_run_integrity_check(
    mock_validate_no_overlaps,
    mock_verify_schema,
    mock_load_schema,
    temp_dir,
    sample_schema
):
    """Test the main integrity check function."""
    # Setup mocks
    mock_load_schema.return_value = sample_schema
    mock_verify_schema.return_value = (True, "Schema compliant")
    mock_validate_no_overlaps.return_value = True

    # Create a test JSON file
    json_file = temp_dir / "test.json"
    json_file.write_text(json.dumps({
        "image_path": "test.jpg",
        "bounding_boxes": [{"x": 10, "y": 10, "w": 20, "h": 20, "id": 1}]
    }))

    summary = run_integrity_check(temp_dir, temp_dir / "schema.yaml")

    assert summary["total_files"] == 1
    assert summary["schema_compliant"] == 1
    assert summary["schema_violations"] == 0
    assert summary["geometry_valid"] == 1
    assert summary["geometry_violations"] == 0
    assert "timestamp" in summary
