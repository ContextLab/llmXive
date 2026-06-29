"""
Contract test for sample data validation.

This test verifies that the sample schema contract correctly validates
sample records from the EMP/MG-RAST datasets.
"""
import pytest
import json
import yaml
import tempfile
import os
from pathlib import Path
import pandas as pd
from jsonschema import ValidationError
from analysis.validation_utils import (
    load_schema,
    validate_record,
    validate_dataframe_records,
    validate_file_against_schema
)


def test_sample_schema_structure():
    """Verify the sample schema file exists and has correct structure."""
    schema_path = Path("specs/contracts/sample.schema.yaml")
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
        
    assert "$schema" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema


def test_sample_schema_validates_correct_record():
    """Test that a valid sample record passes validation."""
    schema_path = Path("specs/contracts/sample.schema.yaml")
    schema = load_schema(schema_path)
    
    valid_sample = {
        "sample_id": "S001",
        "plant_species": "Zea mays",
        "gps_latitude": 40.7128,
        "gps_longitude": -74.0060,
        "soil_type": "Loam",
        "sequencing_depth": 50000
    }
    
    assert validate_record(valid_sample, schema, "sample_schema") is True


def test_sample_schema_rejects_missing_required():
    """Test that a sample record missing required fields fails validation."""
    schema_path = Path("specs/contracts/sample.schema.yaml")
    schema = load_schema(schema_path)
    
    # Missing 'sample_id' which is required
    invalid_sample = {
        "plant_species": "Zea mays",
        "gps_latitude": 40.7128,
        "gps_longitude": -74.0060,
        "soil_type": "Loam",
        "sequencing_depth": 50000
    }
    
    assert validate_record(invalid_sample, schema, "sample_schema") is False


def test_sample_schema_rejects_wrong_type():
    """Test that a sample record with wrong data types fails validation."""
    schema_path = Path("specs/contracts/sample.schema.yaml")
    schema = load_schema(schema_path)
    
    # gps_latitude should be a number, not a string
    invalid_sample = {
        "sample_id": "S001",
        "plant_species": "Zea mays",
        "gps_latitude": "40.7128",  # Wrong type
        "gps_longitude": -74.0060,
        "soil_type": "Loam",
        "sequencing_depth": 50000
    }
    
    assert validate_record(invalid_sample, schema, "sample_schema") is False


def test_sample_schema_validates_dataframe():
    """Test validating a DataFrame of sample records."""
    schema_path = Path("specs/contracts/sample.schema.yaml")
    schema = load_schema(schema_path)
    
    df = pd.DataFrame([
        {
            "sample_id": "S001",
            "plant_species": "Zea mays",
            "gps_latitude": 40.7128,
            "gps_longitude": -74.0060,
            "soil_type": "Loam",
            "sequencing_depth": 50000
        },
        {
            "sample_id": "S002",
            "plant_species": "Glycine max",
            "gps_latitude": 35.0,
            "gps_longitude": -90.0,
            "soil_type": "Clay",
            "sequencing_depth": 45000
        }
    ])
    
    results = validate_dataframe_records(df, schema, "sample_schema", strict=True)
    assert all(r["valid"] for r in results)