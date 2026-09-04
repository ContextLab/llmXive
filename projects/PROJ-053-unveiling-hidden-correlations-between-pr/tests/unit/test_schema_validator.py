import os
import tempfile
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Adjust import based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.schema_validator import load_schema, validate_csv_schema, setup_logger

@pytest.fixture
def temp_schema_file():
    schema_content = {
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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def valid_csv_file():
    data = {
        'laser_power': [200, 300, 400],
        'scan_speed': [500, 600, 700],
        'layer_thickness': [0.03, 0.04, 0.05],
        'yield_strength': [400, 500, 600],
        'ductility': [10, 12, 14]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        pd.DataFrame(data).to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def invalid_csv_missing_col():
    data = {
        'laser_power': [200, 300],
        'scan_speed': [500, 600],
        # Missing layer_thickness
        'yield_strength': [400, 500],
        'ductility': [10, 12]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        pd.DataFrame(data).to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def invalid_csv_non_numeric():
    data = {
        'laser_power': ['high', 'low'], # Non-numeric
        'scan_speed': [500, 600],
        'layer_thickness': [0.03, 0.04],
        'yield_strength': [400, 500],
        'ductility': [10, 12]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        pd.DataFrame(data).to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

def test_load_schema_valid(temp_schema_file):
    schema = load_schema(temp_schema_file)
    assert 'properties' in schema
    assert 'required' in schema
    assert 'laser_power' in schema['properties']

def test_load_schema_missing_file():
    with pytest.raises(FileNotFoundError):
        load_schema("non_existent_file.yaml")

def test_validate_csv_schema_valid(valid_csv_file, temp_schema_file):
    df = pd.read_csv(valid_csv_file)
    schema = load_schema(temp_schema_file)
    logger = setup_logger("test")
    assert validate_csv_schema(df, schema, logger) is True

def test_validate_csv_schema_missing_columns(invalid_csv_missing_col, temp_schema_file):
    df = pd.read_csv(invalid_csv_missing_col)
    schema = load_schema(temp_schema_file)
    logger = setup_logger("test")
    with pytest.raises(ValueError) as exc_info:
        validate_csv_schema(df, schema, logger)
    assert "Missing required columns" in str(exc_info.value)

def test_validate_csv_schema_non_numeric(invalid_csv_non_numeric, temp_schema_file):
    df = pd.read_csv(invalid_csv_non_numeric)
    schema = load_schema(temp_schema_file)
    logger = setup_logger("test")
    with pytest.raises(ValueError) as exc_info:
        validate_csv_schema(df, schema, logger)
    assert "cannot be converted to numeric" in str(exc_info.value)
