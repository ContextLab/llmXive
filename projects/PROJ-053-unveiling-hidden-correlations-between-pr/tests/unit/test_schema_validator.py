import pytest
import pandas as pd
import os
import yaml
from pathlib import Path
import tempfile
import shutil

# Import the module under test
# Assuming the test runs from project root or PYTHONPATH is set correctly
try:
    from data.schema_validator import validate_csv_schema, load_schema
except ImportError:
    # Fallback for direct execution from tests directory
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from data.schema_validator import validate_csv_schema, load_schema

@pytest.fixture
def temp_schema_dir():
    """Create a temporary directory for schema files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def valid_schema_path(temp_schema_dir):
    """Create a valid schema file."""
    schema = {
        "type": "object",
        "properties": {
            "laser_power": {"type": "number"},
            "scan_speed": {"type": "number"},
            "layer_thickness": {"type": "number"},
            "yield_strength": {"type": "number"},
            "ductility": {"type": "number"},
            "fatigue_life": {"type": "number"}
        },
        "required": ["laser_power", "scan_speed", "layer_thickness", "yield_strength", "ductility"]
    }
    path = os.path.join(temp_schema_dir, "test_schema.yaml")
    with open(path, 'w') as f:
        yaml.dump(schema, f)
    return path

@pytest.fixture
def valid_df():
    """Create a valid dataframe."""
    return pd.DataFrame({
        'laser_power': [100.0, 200.0],
        'scan_speed': [500.0, 600.0],
        'layer_thickness': [0.03, 0.04],
        'yield_strength': [300.0, 400.0],
        'ductility': [10.0, 15.0]
    })

@pytest.fixture
def df_missing_column():
    """Create a dataframe missing a required column."""
    return pd.DataFrame({
        'laser_power': [100.0, 200.0],
        'scan_speed': [500.0, 600.0],
        'layer_thickness': [0.03, 0.04],
        'yield_strength': [300.0, 400.0]
        # Missing 'ductility'
    })

@pytest.fixture
def df_non_numeric():
    """Create a dataframe with non-numeric required column."""
    return pd.DataFrame({
        'laser_power': [100.0, 200.0],
        'scan_speed': [500.0, 600.0],
        'layer_thickness': [0.03, 0.04],
        'yield_strength': [300.0, 400.0],
        'ductility': ['high', 'low']  # Non-numeric
    })

def test_validate_csv_schema_success(valid_df, valid_schema_path):
    """Test successful validation."""
    assert validate_csv_schema(valid_df, valid_schema_path) is True

def test_validate_csv_schema_missing_column(df_missing_column, valid_schema_path):
    """Test validation fails when required column is missing."""
    with pytest.raises(ValueError) as excinfo:
        validate_csv_schema(df_missing_column, valid_schema_path)
    assert "Missing required columns" in str(excinfo.value)

def test_validate_csv_schema_non_numeric(df_non_numeric, valid_schema_path):
    """Test validation fails when required column is not numeric."""
    with pytest.raises(ValueError) as excinfo:
        validate_csv_schema(df_non_numeric, valid_schema_path)
    assert "is not numeric" in str(excinfo.value)

def test_load_schema_file_not_found(temp_schema_dir):
    """Test loading a non-existent schema file."""
    with pytest.raises(FileNotFoundError):
        load_schema(os.path.join(temp_schema_dir, "non_existent.yaml"))

def test_validate_csv_schema_optional_column(valid_df, valid_schema_path):
    """Test that optional columns (fatigue_life) are allowed but not required."""
    # Add an optional column
    valid_df_with_optional = valid_df.copy()
    valid_df_with_optional['fatigue_life'] = [1000.0, 2000.0]
    
    # Should still pass
    assert validate_csv_schema(valid_df_with_optional, valid_schema_path) is True

def test_validate_csv_schema_extra_column_warning(valid_df, valid_schema_path):
    """Test that extra columns not in schema are handled (should not raise error based on current impl, but might log warning)."""
    df_extra = valid_df.copy()
    df_extra['extra_col'] = [1, 2]
    # Current implementation logs warning but returns True. 
    # If the requirement is strict, this might need to raise. 
    # Based on T006 description: "verify all required columns exist and contain numeric data".
    # It does not explicitly say "fail on extra columns".
    assert validate_csv_schema(df_extra, valid_schema_path) is True