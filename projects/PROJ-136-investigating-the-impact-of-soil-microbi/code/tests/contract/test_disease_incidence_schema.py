"""
Contract test for disease incidence data validation.

This test verifies that the disease incidence schema contract correctly
validates disease incidence records.
"""
import pytest
import yaml
from pathlib import Path
import pandas as pd
from jsonschema import ValidationError
from analysis.validation_utils import (
    load_schema,
    validate_record,
    validate_dataframe_records
)


def test_disease_incidence_schema_structure():
    """Verify the disease incidence schema file exists and has correct structure."""
    schema_path = Path("specs/contracts/disease_incidence.schema.yaml")
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
        
    assert "$schema" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema


def test_disease_incidence_schema_validates_correct_record():
    """Test that a valid disease incidence record passes validation."""
    schema_path = Path("specs/contracts/disease_incidence.schema.yaml")
    schema = load_schema(schema_path)
    
    valid_record = {
        "sample_id": "S001",
        "disease_type": "Fungal blight",
        "incidence_rate": 0.15,
        "measurement_date": "2023-06-15"
    }
    
    assert validate_record(valid_record, schema, "disease_incidence_schema") is True


def test_disease_incidence_schema_rejects_missing_required():
    """Test that a record missing required fields fails validation."""
    schema_path = Path("specs/contracts/disease_incidence.schema.yaml")
    schema = load_schema(schema_path)
    
    # Missing 'incidence_rate'
    invalid_record = {
        "sample_id": "S001",
        "disease_type": "Fungal blight",
        "measurement_date": "2023-06-15"
    }
    
    assert validate_record(invalid_record, schema, "disease_incidence_schema") is False


def test_disease_incidence_schema_rejects_invalid_range():
    """Test that incidence_rate outside 0-1 range fails validation."""
    schema_path = Path("specs/contracts/disease_incidence.schema.yaml")
    schema = load_schema(schema_path)
    
    # incidence_rate > 1.0
    invalid_record = {
        "sample_id": "S001",
        "disease_type": "Fungal blight",
        "incidence_rate": 1.5,
        "measurement_date": "2023-06-15"
    }
    
    assert validate_record(invalid_record, schema, "disease_incidence_schema") is False


def test_disease_incidence_schema_validates_dataframe():
    """Test validating a DataFrame of disease incidence records."""
    schema_path = Path("specs/contracts/disease_incidence.schema.yaml")
    schema = load_schema(schema_path)
    
    df = pd.DataFrame([
        {
            "sample_id": "S001",
            "disease_type": "Fungal blight",
            "incidence_rate": 0.15,
            "measurement_date": "2023-06-15"
        },
        {
            "sample_id": "S002",
            "disease_type": "Bacterial wilt",
            "incidence_rate": 0.05,
            "measurement_date": "2023-06-20"
        }
    ])
    
    results = validate_dataframe_records(df, schema, "disease_incidence_schema", strict=True)
    assert all(r["valid"] for r in results)