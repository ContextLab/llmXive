"""
Contract tests for dataset schema validation.

These tests verify that the dataset schema defined in 
contracts/dataset.schema.yaml is correctly enforced.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import pytest
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.exceptions import SchemaValidationError
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# Path to schema file
SCHEMA_PATH = project_root / "contracts" / "dataset.schema.yaml"

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and parse the JSON schema from YAML file."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def test_schema_validation_passes(df: pd.DataFrame) -> bool:
    """
    Test that a valid dataframe passes schema validation.
    
    Args:
        df: DataFrame to validate against the schema
        
    Returns:
        True if validation passes
        
    Raises:
        SchemaValidationError: If validation fails
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    schema = load_schema(str(SCHEMA_PATH))
    
    # Convert DataFrame to dict for jsonschema validation
    # jsonschema expects a dict, not a DataFrame
    data_dict = df.to_dict(orient='records')
    
    # Validate each record individually
    # Note: jsonschema.validate can validate a list of objects
    # but we'll validate each record to get better error messages
    for i, record in enumerate(data_dict):
        try:
            # We'll use a simplified validation approach here
            # since jsonschema.validate with a list schema is complex
            # Instead, we check that all required fields exist and have correct types
            required_fields = schema.get('required', [])
            properties = schema.get('properties', {})
            
            for field in required_fields:
                if field not in record:
                    raise SchemaValidationError(
                        f"Record {i}: Missing required field '{field}'"
                    )
                
                # Type checking
                if field in properties:
                    expected_type = properties[field].get('type')
                    value = record[field]
                    
                    if value is not None:
                        # Check type compatibility
                        if expected_type == 'number' and not isinstance(value, (int, float)):
                            raise SchemaValidationError(
                                f"Record {i}: Field '{field}' should be number, got {type(value).__name__}"
                            )
                        elif expected_type == 'string' and not isinstance(value, str):
                            raise SchemaValidationError(
                                f"Record {i}: Field '{field}' should be string, got {type(value).__name__}"
                            )
                        elif expected_type == 'integer' and not isinstance(value, int):
                            # Allow float if it's a whole number
                            if isinstance(value, float) and value.is_integer():
                                record[field] = int(value)
                            else:
                                raise SchemaValidationError(
                                    f"Record {i}: Field '{field}' should be integer, got {type(value).__name__}"
                                )
            
            logger.debug(f"Record {i} passed schema validation")
            
        except SchemaValidationError:
            raise
        except Exception as e:
            raise SchemaValidationError(
                f"Record {i}: Unexpected validation error: {str(e)}"
            )
    
    logger.info("Schema validation passed for all records")
    return True

def test_schema_validation_fails_missing_field() -> None:
    """Test that schema validation fails when a required field is missing."""
    # Create a DataFrame with a missing required field
    df = pd.DataFrame({
        'experiment_id': ['exp1', 'exp2'],
        'source': ['mp', 'nist'],
        # Missing 'material_type' which is required
        'milling_speed': [100, 200],
    })
    
    with pytest.raises(SchemaValidationError) as exc_info:
        test_schema_validation_passes(df)
    
    assert "Missing required field 'material_type'" in str(exc_info.value)
    logger.info("Correctly detected missing required field")

def test_schema_validation_fails_wrong_type() -> None:
    """Test that schema validation fails when a field has wrong type."""
    # Create a DataFrame with wrong type for a field
    df = pd.DataFrame({
        'experiment_id': ['exp1', 'exp2'],
        'source': ['mp', 'nist'],
        'material_type': ['metal', 'ceramic'],
        'milling_speed': [100, 200],
        'milling_time': ['1 hour', '2 hours'],  # Should be number
    })
    
    with pytest.raises(SchemaValidationError) as exc_info:
        test_schema_validation_passes(df)
    
    assert "should be number" in str(exc_info.value)
    logger.info("Correctly detected wrong field type")

def test_schema_validation_with_valid_data() -> None:
    """Test schema validation with a properly formatted DataFrame."""
    # Create a DataFrame with all required fields and correct types
    df = pd.DataFrame({
        'experiment_id': ['exp1', 'exp2'],
        'source': ['mp', 'nist'],
        'source_id': ['mp-123', 'nist-456'],
        'material_type': ['metal', 'ceramic'],
        'milling_speed': [100.0, 200.0],
        'milling_time': [30.0, 60.0],
        'ball_to_powder_ratio': [10.0, 5.0],
        'youngs_modulus': [200.0, 300.0],
        'density': [7.8, 3.9],
        'd10': [10.0, 20.0],
        'd50': [50.0, 100.0],
        'd90': [100.0, 200.0],
        'process_duration': [1.0, 2.0],
    })
    
    # This should not raise any exception
    result = test_schema_validation_passes(df)
    assert result is True
    logger.info("Valid data passed schema validation")

def test_load_schema_file_exists() -> None:
    """Test that the schema file exists and can be loaded."""
    assert SCHEMA_PATH.exists(), f"Schema file not found: {SCHEMA_PATH}"
    
    schema = load_schema(str(SCHEMA_PATH))
    assert 'properties' in schema, "Schema missing 'properties' key"
    assert 'required' in schema, "Schema missing 'required' key"
    
    # Check for expected fields
    expected_fields = [
        'experiment_id', 'source', 'source_id', 'material_type',
        'milling_speed', 'milling_time', 'ball_to_powder_ratio',
        'youngs_modulus', 'density', 'd10', 'd50', 'd90', 'process_duration'
    ]
    
    for field in expected_fields:
        assert field in schema['properties'], f"Schema missing property '{field}'"
    
    logger.info("Schema file loaded and validated successfully")