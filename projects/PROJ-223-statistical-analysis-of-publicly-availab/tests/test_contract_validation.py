import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import yaml

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.schema_validation import validate_merged_dataset, SchemaValidationError
from code.ingest import validate_merged_output

@pytest.fixture
def sample_schema():
    """Create a temporary schema file for testing."""
    schema = {
        "name": "merged_traffic_weather",
        "fields": [
            {"name": "accident_id", "type": "string", "required": True},
            {"name": "severity", "type": "integer", "required": True},
            {"name": "precipitation", "type": "float", "required": True},
            {"name": "visibility", "type": "float", "required": True},
            {"name": "temperature", "type": "float", "required": False}
        ]
    }
    return schema

@pytest.fixture
def valid_dataframe():
    """Create a valid DataFrame matching the schema."""
    return pd.DataFrame({
        "accident_id": ["A1", "A2", "A3"],
        "severity": [1, 2, 3],
        "precipitation": [0.0, 0.5, 1.2],
        "visibility": [10.0, 5.0, 2.0],
        "temperature": [20.0, 15.0, 10.0]
    })

@pytest.fixture
def invalid_dataframe_missing_col():
    """Create a DataFrame missing a required column."""
    return pd.DataFrame({
        "accident_id": ["A1", "A2"],
        "severity": [1, 2],
        "precipitation": [0.0, 0.5],
        # missing visibility
    })

@pytest.fixture
def invalid_dataframe_null_required():
    """Create a DataFrame with null in a required column."""
    return pd.DataFrame({
        "accident_id": ["A1", "A2"],
        "severity": [1, 2],
        "precipitation": [0.0, None], # Null in required float
        "visibility": [10.0, 5.0],
        "temperature": [20.0, 15.0]
    })

def test_validate_merged_output_pass(valid_dataframe, tmp_path):
    """Test that valid data passes validation."""
    schema_path = tmp_path / "schema.yaml"
    schema = {
        "name": "test_schema",
        "fields": [
            {"name": "accident_id", "type": "string", "required": True},
            {"name": "severity", "type": "integer", "required": True},
            {"name": "precipitation", "type": "float", "required": True},
            {"name": "visibility", "type": "float", "required": True},
        ]
    }
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    # Should not raise
    result = validate_merged_output(valid_dataframe, str(schema_path))
    assert result is True

def test_validate_merged_output_missing_column(invalid_dataframe_missing_col, tmp_path):
    """Test that missing required column raises SchemaValidationError."""
    schema_path = tmp_path / "schema.yaml"
    schema = {
        "name": "test_schema",
        "fields": [
            {"name": "accident_id", "type": "string", "required": True},
            {"name": "severity", "type": "integer", "required": True},
            {"name": "precipitation", "type": "float", "required": True},
            {"name": "visibility", "type": "float", "required": True},
        ]
    }
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    with pytest.raises(SchemaValidationError):
        validate_merged_output(invalid_dataframe_missing_col, str(schema_path))

def test_validate_merged_output_null_required(invalid_dataframe_null_required, tmp_path):
    """Test that null in required column raises SchemaValidationError."""
    schema_path = tmp_path / "schema.yaml"
    schema = {
        "name": "test_schema",
        "fields": [
            {"name": "accident_id", "type": "string", "required": True},
            {"name": "severity", "type": "integer", "required": True},
            {"name": "precipitation", "type": "float", "required": True},
            {"name": "visibility", "type": "float", "required": True},
        ]
    }
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    with pytest.raises(SchemaValidationError):
        validate_merged_output(invalid_dataframe_null_required, str(schema_path))