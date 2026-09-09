"""
Unit tests for schema validation logic.
"""
import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_validator import SchemaValidator, validate_artifacts
from config import get_project_root

def test_schema_loading():
    """Test that schemas can be loaded from the contracts directory."""
    project_root = get_project_root()
    dataset_schema_path = project_root / "contracts" / "dataset.schema.yaml"
    output_schema_path = project_root / "contracts" / "output.schema.yaml"

    assert dataset_schema_path.exists(), "Dataset schema file missing"
    assert output_schema_path.exists(), "Output schema file missing"

    dataset_validator = SchemaValidator(str(dataset_schema_path))
    output_validator = SchemaValidator(str(output_schema_path))

    assert dataset_validator.schema is not None
    assert output_validator.schema is not None

def test_valid_record():
    """Test validation of a record that conforms to the schema."""
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    validator = SchemaValidator(str(schema_path))

    valid_record = {
        "age": 25,
        "sex": "M",
        "bmi": 22.5,
        "diet": "Standard",
        "alpha_power": 12.3,
        "taxon_abundances": {
            "Bacteroides": 0.4,
            "Firmicutes": 0.3
        }
    }

    assert validator.validate_record(valid_record) is True

def test_invalid_record_missing_field():
    """Test validation of a record missing a required field."""
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    validator = SchemaValidator(str(schema_path))

    invalid_record = {
        "age": 25,
        "sex": "M",
        # Missing bmi, diet, alpha_power, taxon_abundances
        "taxon_abundances": {"Bacteroides": 0.4}
    }

    assert validator.validate_record(invalid_record) is False

def test_invalid_record_wrong_type():
    """Test validation of a record with wrong data types."""
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    validator = SchemaValidator(str(schema_path))

    invalid_record = {
        "age": "twenty-five",  # Should be int
        "sex": "M",
        "bmi": 22.5,
        "diet": "Standard",
        "alpha_power": 12.3,
        "taxon_abundances": {"Bacteroides": 0.4}
    }

    assert validator.validate_record(invalid_record) is False

def test_validate_artifacts_entry_point():
    """Test the main entry point function."""
    # This should run without crashing if schemas exist
    result = validate_artifacts()
    assert result is True