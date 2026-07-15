"""
Unit tests for dataset configuration validator.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import the module under test
from code.dataset_config_validator import (
    validate_config,
    create_sample_config,
    _validate_config_against_schema,
    _validate_dataset_entry
)


@pytest.fixture
def valid_schema():
    """Return a minimal valid schema for testing."""
    return {
        "type": "object",
        "required": ["version", "datasets"],
        "properties": {
            "version": {"type": "string"},
            "datasets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "source"],
                    "properties": {
                        "id": {"type": "string"},
                        "source": {"type": "string"},
                        "description": {"type": "string"},
                        "metadata": {"type": "object"}
                    }
                }
            }
        }
    }


@pytest.fixture
def valid_config():
    """Return a minimal valid config for testing."""
    return {
        "version": "1.0.0",
        "datasets": [
            {
                "id": "PRJNA123",
                "source": "ncbi_sra",
                "description": "Test dataset",
                "metadata": {"key": "value"}
            }
        ]
    }


@pytest.fixture
def invalid_config_missing_required():
    """Return a config missing required fields."""
    return {
        "version": "1.0.0",
        "datasets": [
            {
                "id": "PRJNA123"
                # Missing 'source' which is required
            }
        ]
    }


def test_validate_config_valid(valid_schema, valid_config, tmp_path):
    """Test validation of a valid config."""
    # Write schema
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("""
type: object
required:
  - version
  - datasets
properties:
  version:
    type: string
  datasets:
    type: array
    items:
type: object
required:
  - id
  - source
properties:
  id:
    type: string
  source:
    type: string
  description:
    type: string
  metadata:
    type: object
""")

    # Write config
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(valid_config))

    is_valid, errors = validate_config(str(config_path), str(schema_path))

    assert is_valid is True
    assert len(errors) == 0


def test_validate_config_missing_required(valid_schema, invalid_config_missing_required, tmp_path):
    """Test validation catches missing required fields."""
    # Write schema
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("""
type: object
required:
  - version
  - datasets
properties:
  version:
    type: string
  datasets:
    type: array
    items:
type: object
required:
  - id
  - source
properties:
  id:
    type: string
  source:
    type: string
""")

    # Write config
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(invalid_config_missing_required))

    is_valid, errors = validate_config(str(config_path), str(schema_path))

    assert is_valid is False
    assert any("source" in error for error in errors)


def test_validate_config_file_not_found(tmp_path):
    """Test validation fails gracefully when config file doesn't exist."""
    non_existent = tmp_path / "non_existent.json"

    is_valid, errors = validate_config(str(non_existent))

    assert is_valid is False
    assert len(errors) == 1
    assert "not found" in errors[0].lower()


def test_validate_config_invalid_json(tmp_path):
    """Test validation fails gracefully for invalid JSON."""
    config_path = tmp_path / "invalid.json"
    config_path.write_text("{ invalid json }")

    is_valid, errors = validate_config(str(config_path))

    assert is_valid is False
    assert len(errors) == 1
    assert "json" in errors[0].lower()


def test_create_sample_config(tmp_path):
    """Test sample config creation."""
    output_path = tmp_path / "sample" / "dataset_ids.json"

    create_sample_config(str(output_path))

    assert output_path.exists()

    with open(output_path, 'r') as f:
        config = json.load(f)

    assert "version" in config
    assert "datasets" in config
    assert len(config["datasets"]) >= 1
    assert config["datasets"][0]["source"] in ["ncbi_sra", "zenodo", "figshare", "dryad"]


def test_validate_dataset_entry_valid():
    """Test validation of a valid dataset entry."""
    dataset = {
        "id": "PRJNA123",
        "source": "ncbi_sra",
        "description": "Test",
        "metadata": {"key": "value"}
    }
    schema = {
        "required": ["id", "source"],
        "properties": {
            "id": {"type": "string"},
            "source": {"type": "string"}
        }
    }

    errors = _validate_dataset_entry(dataset, schema, 0)

    assert len(errors) == 0


def test_validate_dataset_entry_missing_required():
    """Test validation catches missing required fields in dataset entry."""
    dataset = {
        "id": "PRJNA123"
        # Missing 'source'
    }
    schema = {
        "required": ["id", "source"],
        "properties": {}
    }

    errors = _validate_dataset_entry(dataset, schema, 0)

    assert len(errors) == 1
    assert "source" in errors[0]


def test_validate_dataset_entry_invalid_source():
    """Test validation catches invalid source values."""
    dataset = {
        "id": "PRJNA123",
        "source": "invalid_source"
    }
    schema = {
        "required": ["id", "source"],
        "properties": {}
    }

    errors = _validate_dataset_entry(dataset, schema, 0)

    assert len(errors) == 1
    assert "source" in errors[0]


def test_validate_config_against_schema_missing_datasets():
    """Test validation catches missing datasets array."""
    config = {
        "version": "1.0.0"
        # Missing datasets
    }
    schema = {
        "required": ["version", "datasets"],
        "properties": {
            "datasets": {
                "type": "array",
                "items": {}
            }
        }
    }

    errors = _validate_config_against_schema(config, schema)

    assert len(errors) == 1
    assert "datasets" in errors[0]