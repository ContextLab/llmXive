"""
Unit tests for the schema validation functionality.
"""

import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys
import tempfile
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.validate_schema import validate_dataframe, load_schema

@pytest.fixture
def sample_schema():
    return {
        "required_columns": ["material_id", "polarizability", "langmuir_capacity", "henry_constant", "surface_area"],
        "columns": {
            "material_id": {
                "type": "string",
                "nullable": False,
                "constraints": {"unique": True}
            },
            "polarizability": {
                "type": "float",
                "nullable": False,
                "constraints": {"min": 0.0}
            },
            "langmuir_capacity": {
                "type": "float",
                "nullable": False,
                "constraints": {"min": 0.0}
            },
            "henry_constant": {
                "type": "float",
                "nullable": False,
                "constraints": {"min": 0.0}
            },
            "surface_area": {
                "type": "float",
                "nullable": False,
                "constraints": {"min": 0.0}
            }
        }
    }

@pytest.fixture
def valid_dataframe(sample_schema):
    data = {
        "material_id": ["M1", "M2", "M3"],
        "polarizability": [1.2, 2.5, 3.8],
        "langmuir_capacity": [10.5, 20.3, 15.7],
        "henry_constant": [0.1, 0.2, 0.15],
        "surface_area": [500.0, 750.0, 600.0]
    }
    return pd.DataFrame(data)

def test_validate_dataframe_with_valid_data(valid_dataframe, sample_schema):
    """Test that valid data passes validation."""
    report = validate_dataframe(valid_dataframe, sample_schema)
    
    assert report["valid"] is True
    assert report["row_count"] == 3
    assert report["column_count"] == 5
    assert len(report["errors"]) == 0

def test_validate_dataframe_missing_required_columns(valid_dataframe, sample_schema):
    """Test validation fails when required columns are missing."""
    # Remove a required column
    df = valid_dataframe.drop(columns=["material_id"])
    report = validate_dataframe(df, sample_schema)
    
    assert report["valid"] is False
    assert any("material_id" in error for error in report["errors"])

def test_validate_dataframe_null_values(valid_dataframe, sample_schema):
    """Test validation fails when non-nullable columns have null values."""
    # Add null values to a non-nullable column
    df = valid_dataframe.copy()
    df.loc[0, "material_id"] = None
    report = validate_dataframe(df, sample_schema)
    
    assert report["valid"] is False
    assert any("material_id" in error and "null" in error for error in report["errors"])

def test_validate_dataframe_constraint_violation(valid_dataframe, sample_schema):
    """Test validation fails when value constraints are violated."""
    # Add values below minimum constraint
    df = valid_dataframe.copy()
    df.loc[0, "polarizability"] = -1.0
    report = validate_dataframe(df, sample_schema)
    
    assert report["valid"] is False
    assert any("polarizability" in error and "minimum" in error for error in report["errors"])

def test_validate_dataframe_duplicate_values(valid_dataframe, sample_schema):
    """Test validation fails when unique constraint is violated."""
    # Add duplicate values to unique column
    df = valid_dataframe.copy()
    df.loc[1, "material_id"] = "M1"
    report = validate_dataframe(df, sample_schema)
    
    assert report["valid"] is False
    assert any("material_id" in error and "unique" in error for error in report["errors"])

def test_validate_dataframe_type_warning(valid_dataframe, sample_schema):
    """Test that type mismatches generate warnings (not errors)."""
    # Create dataframe with integer instead of float for a float column
    df = valid_dataframe.copy()
    df["polarizability"] = df["polarizability"].astype(int)
    report = validate_dataframe(df, sample_schema)
    
    # Should have a warning about type mismatch
    assert any("polarizability" in warning and "float" in warning for warning in report["warnings"])

def test_load_schema_from_yaml():
    """Test loading a schema from a YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"required_columns": ["col1"]}, f)
        temp_path = f.name
    
    try:
        schema = load_schema(temp_path)
        assert "required_columns" in schema
        assert schema["required_columns"] == ["col1"]
    finally:
        Path(temp_path).unlink()
