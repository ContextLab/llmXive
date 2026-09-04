import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import load_schema, validate_schema
from config import CONTRACTS_DIR

@pytest.fixture
def valid_schema():
    return load_schema(str(CONTRACTS_DIR / "raw_halo.schema.yaml"))

@pytest.fixture
def valid_data():
    # Create a valid dataframe matching the schema
    n = 10
    data = {
        'mass': [1e12 + i for i in range(n)],
        'particle_count': [300 + i for i in range(n)],
        'position': [[1.0, 2.0, 3.0] for _ in range(n)],
        'velocity': [[10.0, 20.0, 30.0] for _ in range(n)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_data_missing_col():
    # Missing 'velocity'
    n = 10
    data = {
        'mass': [1e12 + i for i in range(n)],
        'particle_count': [300 + i for i in range(n)],
        'position': [[1.0, 2.0, 3.0] for _ in range(n)],
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_data_wrong_type():
    # 'mass' contains strings
    n = 10
    data = {
        'mass': ["not a number" for _ in range(n)],
        'particle_count': [300 + i for i in range(n)],
        'position': [[1.0, 2.0, 3.0] for _ in range(n)],
        'velocity': [[10.0, 20.0, 30.0] for _ in range(n)]
    }
    return pd.DataFrame(data)

def test_load_schema_exists(valid_schema):
    assert valid_schema is not None
    assert valid_schema['type'] == 'object'
    assert 'mass' in valid_schema['properties']

def test_validate_schema_passes(valid_schema, valid_data):
    # Should not raise
    result = validate_schema(valid_data, valid_schema)
    assert result is True

def test_validate_schema_fails_missing_col(valid_schema, invalid_data_missing_col):
    with pytest.raises(Exception):
        validate_schema(invalid_data_missing_col, valid_schema)

def test_validate_schema_fails_wrong_type(valid_schema, invalid_data_wrong_type):
    with pytest.raises(Exception):
        validate_schema(invalid_data_wrong_type, valid_schema)

def test_validate_schema_particle_count_boundary(valid_schema):
    # Test boundary: exactly 300 particles (should pass schema validation, 
    # though filtering logic is separate, schema requires min 0)
    data = {
        'mass': [1e12],
        'particle_count': [300],
        'position': [[1.0, 2.0, 3.0]],
        'velocity': [[10.0, 20.0, 30.0]]
    }
    df = pd.DataFrame(data)
    assert validate_schema(df, valid_schema) is True

    # Test 0 particles (schema allows >= 0)
    data_zero = {
        'mass': [1e12],
        'particle_count': [0],
        'position': [[1.0, 2.0, 3.0]],
        'velocity': [[10.0, 20.0, 30.0]]
    }
    df_zero = pd.DataFrame(data_zero)
    assert validate_schema(df_zero, valid_schema) is True