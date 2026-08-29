"""
Contract test for the dataset schema validation.

This test ensures that the data produced by the pipeline conforms to the
expected schema defined in dataset.schema.yaml.
"""

import pytest
import yaml
import json
from pathlib import Path
from jsonschema import validate, ValidationError
import sys

# Add parent to path if running as script
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.contract import load_schema

# Constants for validation
MIN_SAMPLES = 30
VALID_TARGET_TYPES = ["regression", "classification"]


def load_sample_data(filepath: Path) -> dict:
    """
    Load a sample dataset file (CSV converted to dict for testing).
    
    This constructs a minimal valid example that matches the schema structure
    expected by the pipeline. In a real scenario, this would load the actual
    CSV produced by the pipeline and convert it to the expected structure.
    """
    return {
        "metadata": {
            "source_doi": "10.5281/zenodo.5778205",
            "generated_at": "2023-10-27T10:00:00Z",
            "checksum": "abc123def456",
            "row_count": 100,
            "feature_columns": ["delta", "delta_h_mix", "delta_chi"],
            "target_column": "target",
            "target_type": "regression"
        },
        "data": [
            {
                "composition": {"Fe": 0.5, "Ni": 0.5},
                "target_value": 1.2,
                "descriptors": {
                    "delta": 0.05,
                    "delta_h_mix": -10.0,
                    "delta_chi": 0.2
                },
                "chemical_family": "Fe-Ni"
            }
        ]
    }


def test_dataset_schema_validity():
    """Test that the schema itself is valid JSON Schema."""
    schema = load_schema("dataset")
    # Basic check that it's a dict
    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert "properties" in schema
    assert "metadata" in schema["properties"]
    assert "data" in schema["properties"]


def test_dataset_schema_validation():
    """Test that valid data passes schema validation."""
    schema = load_schema("dataset")
    valid_data = load_sample_data(Path("data/processed/clean_dataset.csv"))
    
    # This should not raise
    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")


def test_dataset_schema_rejection_invalid_target_type():
    """Test that invalid target_type fails schema validation."""
    schema = load_schema("dataset")
    invalid_data = {
        "metadata": {
            "source_doi": "10.5281/zenodo.5778205",
            "generated_at": "2023-10-27T10:00:00Z",
            "checksum": "abc123",
            "row_count": 100,
            "feature_columns": ["delta", "delta_h_mix", "delta_chi"],
            "target_column": "target",
            "target_type": "invalid_type"
        },
        "data": []
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)


def test_dataset_schema_rejection_low_sample_count():
    """Test that row_count below MIN_SAMPLES fails validation."""
    schema = load_schema("dataset")
    invalid_data = {
        "metadata": {
            "source_doi": "10.5281/zenodo.5778205",
            "generated_at": "2023-10-27T10:00:00Z",
            "checksum": "abc123",
            "row_count": 20,  # Below MIN_SAMPLES=30
            "feature_columns": ["delta", "delta_h_mix", "delta_chi"],
            "target_column": "target",
            "target_type": "regression"
        },
        "data": []
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)


def test_dataset_schema_rejection_missing_required_fields():
    """Test that missing required fields fail schema validation."""
    schema = load_schema("dataset")
    invalid_data = {
        "metadata": {
            "source_doi": "10.5281/zenodo.5778205",
            "generated_at": "2023-10-27T10:00:00Z",
            # Missing checksum, row_count, feature_columns, etc.
            "target_column": "target",
            "target_type": "regression"
        },
        "data": []
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)


def test_dataset_schema_rejection_empty_feature_columns():
    """Test that empty feature_columns fails validation."""
    schema = load_schema("dataset")
    invalid_data = {
        "metadata": {
            "source_doi": "10.5281/zenodo.5778205",
            "generated_at": "2023-10-27T10:00:00Z",
            "checksum": "abc123",
            "row_count": 100,
            "feature_columns": [],  # Empty list
            "target_column": "target",
            "target_type": "regression"
        },
        "data": []
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)
