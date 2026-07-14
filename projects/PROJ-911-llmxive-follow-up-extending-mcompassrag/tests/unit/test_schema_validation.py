"""
Unit tests for schema validation functionality.
"""
import json
import yaml
import pytest
from pathlib import Path
import tempfile
import os

# Import the module under test
from code.validate_schemas import validate_artifact, load_schema

# Test fixtures
VALID_DATASET = {
    "metadata": {
        "source": "hotpotqa",
        "version": "1.0",
        "sample_size": 10,
        "generated_at": "2023-10-01T12:00:00Z",
        "seed": 42
    },
    "records": [
        {"id": "doc1", "text": "Sample text 1", "title": "Title 1"},
        {"id": "doc2", "text": "Sample text 2", "title": "Title 2"}
    ]
}

INVALID_DATASET_MISSING_FIELDS = {
    "metadata": {
        "source": "hotpotqa",
        # Missing version, sample_size, etc.
    },
    "records": []
}

VALID_OUTPUT = {
    "metadata": {
        "task_id": "T013",
        "pipeline_version": "1.0.0",
        "generated_at": "2023-10-01T12:00:00Z"
    },
    "items": [
        {"doc_id": "doc1", "nodes": 5, "edges": 10, "modularity": 0.5}
    ]
}

def test_load_schema_valid():
    """Test loading a valid schema file."""
    schema = load_schema("dataset.schema.yaml")
    assert "properties" in schema
    assert "metadata" in schema["properties"]

def test_validate_dataset_valid():
    """Test validation of a valid dataset artifact."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(VALID_DATASET, f)
        temp_path = Path(f.name)
    
    try:
        is_valid, error = validate_artifact(temp_path, "dataset.schema.yaml")
        assert is_valid is True
        assert error is None
    finally:
        os.unlink(temp_path)

def test_validate_dataset_invalid():
    """Test validation of an invalid dataset artifact."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(INVALID_DATASET_MISSING_FIELDS, f)
        temp_path = Path(f.name)
    
    try:
        is_valid, error = validate_artifact(temp_path, "dataset.schema.yaml")
        assert is_valid is False
        assert error is not None
        assert "sample_size" in error
    finally:
        os.unlink(temp_path)

def test_validate_output_valid():
    """Test validation of a valid output artifact."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(VALID_OUTPUT, f)
        temp_path = Path(f.name)
    
    try:
        is_valid, error = validate_artifact(temp_path, "output.schema.yaml")
        assert is_valid is True
        assert error is None
    finally:
        os.unlink(temp_path)

def test_validate_nonexistent_file():
    """Test validation of a non-existent file."""
    fake_path = Path("/tmp/does_not_exist.json")
    is_valid, error = validate_artifact(fake_path, "dataset.schema.yaml")
    assert is_valid is False
    assert "not found" in error.lower() or "file" in error.lower()

def test_validate_invalid_json():
    """Test validation of a file with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)
    
    try:
        is_valid, error = validate_artifact(temp_path, "dataset.schema.yaml")
        assert is_valid is False
        assert "JSON" in error
    finally:
        os.unlink(temp_path)

def test_load_schema_nonexistent():
    """Test loading a non-existent schema file."""
    with pytest.raises(FileNotFoundError):
        load_schema("nonexistent.schema.yaml")
