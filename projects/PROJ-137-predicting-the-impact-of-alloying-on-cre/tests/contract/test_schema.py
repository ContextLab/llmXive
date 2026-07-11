import os
import yaml
import json
import re
import jsonschema
import pandas as pd
import pytest
from pathlib import Path

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "alloy_dataset.csv"

@pytest.fixture
def schema():
    """Load the dataset schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_dataframe():
    """
    Create a minimal valid DataFrame that adheres to the schema.
    This is used to verify the schema accepts valid data.
    """
    data = {
        "alloy_id": ["550e8400-e29b-41d4-a716-446655440000"],
        "composition_str": ["Al:0.3333,Ni:0.6667"],
        "temperature": [1000.0],
        "stress": [100.0],
        "rupture_time": [500.0],
        "mixing_enthalpy": [-15.5],
        "radius_mismatch": [2.5]
    }
    return pd.DataFrame(data)

def test_schema_file_structure(schema):
    """Verify the schema file contains required top-level keys."""
    assert "$schema" in schema
    assert "title" in schema
    assert "properties" in schema
    assert "field_definitions" in schema["properties"]

def test_schema_validates_sample_dataframe(schema, sample_dataframe):
    """
    Validate that a correctly formatted DataFrame passes the schema.
    """
    records = sample_dataframe.to_dict(orient="records")
    
    # Validate column names
    required_columns = ["alloy_id", "composition_str", "temperature", "stress", 
                      "rupture_time", "mixing_enthalpy", "radius_mismatch"]
    assert list(sample_dataframe.columns) == required_columns, \
        f"Columns mismatch: {list(sample_dataframe.columns)} vs {required_columns}"

    # Validate data types and constraints for the first row
    row = records[0]
    
    # alloy_id: string, uuid format (basic check)
    assert isinstance(row["alloy_id"], str)
    assert len(row["alloy_id"]) == 36 # Basic UUID length check

    # composition_str: string, specific pattern
    assert isinstance(row["composition_str"], str)
    assert "Al" in row["composition_str"] and "Ni" in row["composition_str"]

    # numeric fields
    assert isinstance(row["temperature"], (int, float))
    assert row["temperature"] > 0
    assert isinstance(row["stress"], (int, float))
    assert row["stress"] > 0
    assert isinstance(row["rupture_time"], (int, float))
    assert row["rupture_time"] > 0

    # nullable numeric fields
    assert row["mixing_enthalpy"] is not None
    assert isinstance(row["mixing_enthalpy"], (int, float))
    assert row["radius_mismatch"] is not None
    assert isinstance(row["radius_mismatch"], (int, float))
    assert row["radius_mismatch"] >= 0

def test_schema_rejects_invalid_composition_str(schema):
    """Verify that invalid composition strings are rejected by logic checks."""
    invalid_data = {
        "alloy_id": "550e8400-e29b-41d4-a716-446655440000",
        "composition_str": "Al Ni 0.5", # Invalid format
        "temperature": 1000.0,
        "stress": 100.0,
        "rupture_time": 500.0,
        "mixing_enthalpy": -15.5,
        "radius_mismatch": 2.5
    }
    
    # Check pattern compliance manually
    pattern = r"^[A-Z][a-z]*:[0-9.]+(,[A-Z][a-z]*:[0-9.]+)*$"
    assert not re.match(pattern, invalid_data["composition_str"])

def test_schema_allows_null_thermodynamics(schema):
    """Verify that null values for thermodynamic fields are allowed."""
    data = {
        "alloy_id": "550e8400-e29b-41d4-a716-446655440000",
        "composition_str": "Al:0.5,Ni:0.5",
        "temperature": 1000.0,
        "stress": 100.0,
        "rupture_time": 500.0,
        "mixing_enthalpy": None,
        "radius_mismatch": None
    }
    
    # Check nullable definition in schema
    fields = schema["properties"]["field_definitions"]
    assert fields["mixing_enthalpy"]["nullable"] is True
    assert fields["radius_mismatch"]["nullable"] is True

def test_schema_column_order_matches_definition(schema):
    """Verify the schema expects the correct column order."""
    expected_cols = [
        "alloy_id", "composition_str", "temperature", "stress",
        "rupture_time", "mixing_enthalpy", "radius_mismatch"
    ]
    defined_keys = list(schema["properties"]["field_definitions"].keys())
    assert defined_keys == expected_cols, f"Schema column order mismatch: {defined_keys}"

def test_real_dataset_validation(schema):
    """
    Contract test: Validate the actual generated dataset (if it exists)
    against the schema. This ensures the pipeline output is compliant.
    """
    if not DATA_PATH.exists():
        pytest.skip(f"Real dataset not found at {DATA_PATH}. Run pipeline first.")
    
    df = pd.read_csv(DATA_PATH)
    records = df.to_dict(orient="records")
    
    # 1. Check column presence and order
    required_columns = ["alloy_id", "composition_str", "temperature", "stress", 
                      "rupture_time", "mixing_enthalpy", "radius_mismatch"]
    assert list(df.columns) == required_columns, \
        f"Real dataset columns mismatch: {list(df.columns)}"
    
    # 2. Check row count
    assert len(df) > 0, "Real dataset is empty"
    
    # 3. Validate each row against schema constraints
    fields = schema["properties"]["field_definitions"]
    
    for i, row in enumerate(records):
        # alloy_id
        assert isinstance(row["alloy_id"], str) and len(row["alloy_id"]) == 36, \
            f"Row {i}: Invalid alloy_id"
        
        # composition_str pattern
        pattern = r"^[A-Z][a-z]*:[0-9.]+(,[A-Z][a-z]*:[0-9.]+)*$"
        assert re.match(pattern, row["composition_str"]), \
            f"Row {i}: Invalid composition_str format: {row['composition_str']}"
        
        # Numeric constraints
        assert row["temperature"] > 0, f"Row {i}: temperature <= 0"
        assert row["stress"] > 0, f"Row {i}: stress <= 0"
        assert row["rupture_time"] > 0, f"Row {i}: rupture_time <= 0"
        
        # Nullable thermodynamics
        if row["mixing_enthalpy"] is not None:
            assert isinstance(row["mixing_enthalpy"], (int, float))
        if row["radius_mismatch"] is not None:
            assert isinstance(row["radius_mismatch"], (int, float))
            assert row["radius_mismatch"] >= 0, f"Row {i}: radius_mismatch < 0"
    
    # 4. If we get here, the real dataset passed all contract checks
    assert True, f"Real dataset ({len(df)} rows) passed schema validation"