"""
Contract test for dataset schema validation (US1).

This test verifies that the dataset schema validation logic correctly
identifies required fields and enforces the schema defined in
`contracts/dataset.schema.yaml`.

It validates the integration between the schema validator utilities
and the actual dataset structure expected by User Story 1.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import pandas as pd
import yaml

# Add project root to path to allow imports of sibling modules
# Assuming this test is run from the project root or via pytest discovery
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.schema_validator import (
    load_schema,
    validate_dataset_schema,
    SchemaValidationError,
    get_missing_fields,
)


# Fixtures
@pytest.fixture
def schema_path() -> Path:
    """Return the path to the dataset schema file."""
    return project_root / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def valid_schema_dict() -> Dict[str, Any]:
    """Return a valid schema dictionary matching the project's expected structure."""
    return {
        "type": "object",
        "properties": {
            "dialogue_id": {"type": "string"},
            "user_id": {"type": "string"},
            "utterance": {"type": "string"},
            "quality_rating": {"type": "integer", "minimum": 1, "maximum": 5},
            "age": {"type": "integer", "minimum": 18, "maximum": 100},
            "gender": {"type": "string", "enum": ["M", "F", "Other", "Unknown"]},
            "politeness_score": {"type": "number"},
        },
        "required": ["dialogue_id", "user_id", "utterance", "quality_rating"],
    }

@pytest.fixture
def valid_dataframe() -> pd.DataFrame:
    """Return a DataFrame that strictly adheres to the valid schema."""
    return pd.DataFrame([
        {
            "dialogue_id": "d1",
            "user_id": "u1",
            "utterance": "Hello there!",
            "quality_rating": 4,
            "age": 25,
            "gender": "F",
            "politeness_score": 0.85,
        },
        {
            "dialogue_id": "d1",
            "user_id": "u1",
            "utterance": "How are you?",
            "quality_rating": 5,
            "age": 25,
            "gender": "F",
            "politeness_score": 0.92,
        },
    ])

@pytest.fixture
def missing_fields_dataframe() -> pd.DataFrame:
    """Return a DataFrame missing required fields (quality_rating)."""
    return pd.DataFrame([
        {
            "dialogue_id": "d2",
            "user_id": "u2",
            "utterance": "Missing rating",
            "age": 30,
            "gender": "M",
        }
    ])

@pytest.fixture
def invalid_type_dataframe() -> pd.DataFrame:
    """Return a DataFrame with an invalid type for a required field."""
    return pd.DataFrame([
        {
            "dialogue_id": "d3",
            "user_id": "u3",
            "utterance": "Bad type",
            "quality_rating": "high",  # Should be integer
            "age": 22,
            "gender": "F",
        }
    ])

# Tests
def test_load_schema_exists(schema_path: Path):
    """Test that the schema file exists and can be loaded."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"
    schema = load_schema(schema_path)
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "required" in schema

def test_validate_dataset_schema_passes(valid_schema_dict: Dict[str, Any], valid_dataframe: pd.DataFrame):
    """Test that a valid DataFrame passes schema validation."""
    # Create a temporary file to hold the schema for the validator
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_schema_dict, f)
        temp_schema_path = f.name

    try:
        # Load the schema from the temp file to mimic real usage
        loaded_schema = load_schema(temp_schema_path)
        # Validate the dataframe against the schema
        result = validate_dataset_schema(valid_dataframe, loaded_schema)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    finally:
        os.unlink(temp_schema_path)

def test_validate_dataset_schema_missing_fields(missing_fields_dataframe: pd.DataFrame, valid_schema_dict: Dict[str, Any]):
    """Test that a DataFrame with missing required fields fails validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_schema_dict, f)
        temp_schema_path = f.name

    try:
        loaded_schema = load_schema(temp_schema_path)
        result = validate_dataset_schema(missing_fields_dataframe, loaded_schema)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        # Check that the error mentions the missing field
        error_messages = [e["message"] for e in result["errors"]]
        assert any("quality_rating" in msg for msg in error_messages)
    finally:
        os.unlink(temp_schema_path)

def test_validate_dataset_schema_invalid_type(invalid_type_dataframe: pd.DataFrame, valid_schema_dict: Dict[str, Any]):
    """Test that a DataFrame with invalid types fails validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_schema_dict, f)
        temp_schema_path = f.name

    try:
        loaded_schema = load_schema(temp_schema_path)
        result = validate_dataset_schema(invalid_type_dataframe, loaded_schema)
        assert result["valid"] is False
        # Check for type mismatch error
        error_messages = [e["message"] for e in result["errors"]]
        assert any("quality_rating" in msg and ("type" in msg or "integer" in msg) for msg in error_messages)
    finally:
        os.unlink(temp_schema_path)

def test_get_missing_fields_valid(valid_dataframe: pd.DataFrame, valid_schema_dict: Dict[str, Any]):
    """Test that get_missing_fields returns an empty list for valid data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_schema_dict, f)
        temp_schema_path = f.name

    try:
        loaded_schema = load_schema(temp_schema_path)
        missing = get_missing_fields(valid_dataframe, loaded_schema)
        assert missing == []
    finally:
        os.unlink(temp_schema_path)

def test_get_missing_fields_invalid(missing_fields_dataframe: pd.DataFrame, valid_schema_dict: Dict[str, Any]):
    """Test that get_missing_fields returns the missing required fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_schema_dict, f)
        temp_schema_path = f.name

    try:
        loaded_schema = load_schema(temp_schema_path)
        missing = get_missing_fields(missing_fields_dataframe, loaded_schema)
        assert "quality_rating" in missing
    finally:
        os.unlink(temp_schema_path)

def test_schema_validation_integration_with_project_schema(schema_path: Path):
    """
    Integration test: Validate a synthetic dataset against the ACTUAL project schema.
    This ensures the project's schema definition is consistent with the validator logic.
    """
    if not schema_path.exists():
        pytest.skip("Project schema file not found; skipping integration test.")

    schema = load_schema(schema_path)
    
    # Create a synthetic valid dataset based on the schema's required fields
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    data = []
    row = {}
    for field in required_fields:
        prop = properties.get(field, {})
        ptype = prop.get("type", "string")
        if ptype == "string":
            row[field] = "test_value"
        elif ptype == "integer":
            row[field] = 1
        elif ptype == "number":
            row[field] = 1.0
        else:
            row[field] = "test_value"
    
    # Add optional fields if defined
    for field in properties:
        if field not in row:
            prop = properties[field]
            ptype = prop.get("type", "string")
            if ptype == "string":
                row[field] = "opt_value"
            elif ptype == "integer":
                row[field] = 2
            elif ptype == "number":
                row[field] = 2.0
    
    df = pd.DataFrame([row])
    
    result = validate_dataset_schema(df, schema)
    
    # We expect this to pass if the schema is well-formed and the data matches
    assert result["valid"] is True, f"Validation failed for valid synthetic data: {result['errors']}"
    assert len(result["errors"]) == 0