import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from code.data.preprocess import validate_schema, load_schema

def test_validate_schema_success():
    """Test that a valid dataframe passes schema validation."""
    # Create a mock dataframe matching the schema
    df = pd.DataFrame({
        'halo_id': [1, 2, 3],
        'mass': [1e12, 1e13, 1e14],
        'x': [0.0, 1.0, 2.0],
        'y': [0.0, 1.0, 2.0],
        'z': [0.0, 1.0, 2.0],
        'vx': [0.0, 1.0, 2.0],
        'vy': [0.0, 1.0, 2.0],
        'vz': [0.0, 1.0, 2.0],
        'num_particles': [500, 1000, 2000]
    })
    
    # Schema is defined in code/contracts/halo.schema.yaml
    # We pass the path explicitly or rely on the default
    result = validate_schema(df, schema_path="code/contracts/halo.schema.yaml")
    assert result is True

def test_validate_schema_missing_column():
    """Test that a dataframe with missing required columns raises ValueError."""
    df = pd.DataFrame({
        'halo_id': [1, 2],
        'mass': [1e12, 1e13]
        # Missing x, y, z, num_particles etc.
    })
    
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_schema(df, schema_path="code/contracts/halo.schema.yaml")

def test_validate_schema_type_mismatch():
    """Test that type mismatches are logged (warning) but don't necessarily crash, 
    depending on strictness. The current implementation logs warnings."""
    df = pd.DataFrame({
        'halo_id': [1, 2],
        'mass': ['not_a_number', 'also_not'], # Should be number
        'x': [0.0, 1.0],
        'y': [0.0, 1.0],
        'z': [0.0, 1.0],
        'vx': [0.0, 1.0],
        'vy': [0.0, 1.0],
        'vz': [0.0, 1.0],
        'num_particles': [500, 1000]
    })
    
    # The current implementation logs a warning but returns True.
    # If the spec requires strict failure on type mismatch, we would expect an exception.
    # Based on the implementation: "logger.warning ... return True"
    result = validate_schema(df, schema_path="code/contracts/halo.schema.yaml")
    assert result is True

def test_load_schema_exists():
    """Test that the schema file can be loaded."""
    schema = load_schema("code/contracts/halo.schema.yaml")
    assert 'required' in schema
    assert 'properties' in schema
    assert 'halo_id' in schema['properties']
