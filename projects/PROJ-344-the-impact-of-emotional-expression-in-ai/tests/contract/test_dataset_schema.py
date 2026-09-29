"""
Contract test for dataset schema validation.
Validates that the generated/loaded dataset complies with the schema defined in contracts/dataset_schema.yaml.
"""
import os
import sys
import pytest
import yaml
import pandas as pd
from pathlib import Path

# Ensure project root is in path to import validators
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from validators import (
    load_schema,
    validate_schema_compliance,
    validate_dataset,
    ValidationError
)
from code.logging_config import get_logger

logger = get_logger("contract_test_dataset_schema")

# Path to the schema file as defined in the project structure
SCHEMA_PATH = project_root / "specs" / "001-emotional-synchrony-trust" / "contracts" / "dataset_schema.yaml"

def test_schema_loads_correctly():
    """Ensure the schema file exists and loads without error."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    schema = load_schema(str(SCHEMA_PATH))
    assert schema is not None
    assert "properties" in schema, "Schema must define properties"
    assert "required" in schema, "Schema must define required fields"

def _create_minimal_valid_dataset(schema: dict) -> pd.DataFrame:
    """
    Constructs a minimal valid DataFrame based on the schema definition.
    This ensures the test data strictly adheres to the contract.
    """
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    data_map = {}

    for field_name in required_fields:
        if field_name in properties:
            field_spec = properties[field_name]
            field_type = field_spec.get("type", "string")
            
            if field_type == "integer":
                data_map[field_name] = [100] # Default integer
            elif field_type == "number":
                # Handle constraints like min/max if present
                min_val = field_spec.get("minimum", 0)
                max_val = field_spec.get("maximum", 100)
                data_map[field_name] = [min_val + (max_val - min_val) / 2]
            elif field_type == "boolean":
                data_map[field_name] = [True]
            elif field_type == "array":
                data_map[field_name] = [["item"]]
            elif field_type == "string":
                # Handle enums
                if "enum" in field_spec:
                    data_map[field_name] = [field_spec["enum"][0]]
                elif "pattern" in field_spec:
                    # Provide a string matching the pattern (simplified)
                    if "interaction_id" in field_name:
                        data_map[field_name] = ["test_001"]
                    elif "timestamp" in field_name:
                        data_map[field_name] = ["2023-01-01T00:00:00"]
                    else:
                        data_map[field_name] = ["valid_string"]
                else:
                    data_map[field_name] = ["default_value"]
        else:
            # Fallback if required field not in properties (shouldn't happen in valid schema)
            data_map[field_name] = ["fallback"]

    return pd.DataFrame(data_map)

def test_validate_dataset_compliance():
    """
    Test the validation logic against a minimal valid dataset constructed from the schema.
    """
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    schema = load_schema(str(SCHEMA_PATH))
    
    df = _create_minimal_valid_dataset(schema)
    
    # Run validation
    try:
        is_valid = validate_dataset(df, schema)
        assert is_valid, "Minimal dataset constructed from schema should pass validation"
    except ValidationError as e:
        # If validation fails, it indicates a mismatch between the schema definition
        # and the validator's expectations, or the test data construction is insufficient.
        logger.error(f"Validation failed for minimal valid data: {e}")
        pytest.fail(f"Schema validation failed for data constructed from schema: {e}")

def test_validate_invalid_dataset_missing_required():
    """Test that validation fails for a dataset missing required fields."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    schema = load_schema(str(SCHEMA_PATH))
    
    # Create a dataset missing a required field.
    # We construct a minimal valid one first, then remove a required column.
    valid_df = _create_minimal_valid_dataset(schema)
    required_cols = schema.get("required", [])
    
    if len(required_cols) > 0:
        # Remove the first required column to simulate missing data
        col_to_remove = required_cols[0]
        if col_to_remove in valid_df.columns:
            invalid_df = valid_df.drop(columns=[col_to_remove])
            
            try:
                is_valid = validate_dataset(invalid_df, schema)
                # If the validator is lenient and returns False instead of raising, we assert that too
                assert not is_valid, "Validation should fail for missing required field"
            except ValidationError:
                # Expected behavior: validator raises an error
                pass
            except Exception as e:
                pytest.fail(f"Unexpected error during validation of invalid dataset: {e}")

def test_validate_invalid_data_types():
    """Test that validation fails for incorrect data types."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    schema = load_schema(str(SCHEMA_PATH))
    
    # Create a valid dataframe
    valid_df = _create_minimal_valid_dataset(schema)
    
    # Corrupt a numeric field to be a string
    if "trust_score" in valid_df.columns:
        valid_df["trust_score"] = "invalid_string"
        
        try:
            is_valid = validate_dataset(valid_df, schema)
            assert not is_valid, "Validation should fail for incorrect data type"
        except ValidationError:
            # Expected
            pass
        except Exception as e:
            pytest.fail(f"Unexpected error during type validation: {e}")