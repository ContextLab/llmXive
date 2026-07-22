import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingest import validate_schema, normalize_columns

@pytest.fixture
def sample_df_valid():
    data = {
        'condition': ['ignored', 'control', 'excluded', 'normal'],
        'prosocial_amount': [10.5, 12.0, 8.0, 15.0],
        'randomized': ['yes', 'no', 'yes', 'no']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing_col():
    data = {
        'condition': ['ignored', 'control'],
        'prosocial_amount': [10.5, 12.0]
        # Missing 'randomized'
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_all_null_condition():
    data = {
        'condition': [np.nan, np.nan],
        'prosocial_amount': [10.5, 12.0],
        'randomized': ['yes', 'no']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_non_numeric_amount():
    data = {
        'condition': ['ignored', 'control'],
        'prosocial_amount': ['ten', 'twelve'],
        'randomized': ['yes', 'no']
    }
    return pd.DataFrame(data)

@pytest.fixture
def logger():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger("test_ingest")

def test_validate_schema_success(sample_df_valid, logger):
    is_valid, msg = validate_schema(sample_df_valid, "test_source", logger)
    assert is_valid is True
    assert msg == ""

def test_validate_schema_missing_columns(sample_df_missing_col, logger):
    is_valid, msg = validate_schema(sample_df_missing_col, "test_source", logger)
    assert is_valid is False
    assert "Missing required columns" in msg
    assert "randomized" in msg

def test_validate_schema_all_null_column(sample_df_all_null_condition, logger):
    is_valid, msg = validate_schema(sample_df_all_null_condition, "test_source", logger)
    assert is_valid is False
    assert "entirely null" in msg

def test_validate_schema_non_numeric_coerceable(sample_df_non_numeric_amount, logger):
    # If it can be coerced, it should pass schema validation (coercion happens inside or before)
    # Our implementation attempts to coerce inside validate_schema
    is_valid, msg = validate_schema(sample_df_non_numeric_amount, "test_source", logger)
    # Note: 'ten' cannot be coerced to float, so it should fail
    assert is_valid is False
    assert "not numeric" in msg or "cannot be coerced" in msg

def test_normalize_columns_mapping(sample_df_valid, logger):
    df, mappings = normalize_columns(sample_df_valid, "test_source", logger)
    
    # Check condition mapping
    assert df['condition'].iloc[0] == 1  # ignored -> 1
    assert df['condition'].iloc[1] == 0  # control -> 0
    assert df['condition'].iloc[2] == 1  # excluded -> 1
    assert df['condition'].iloc[3] == 0  # normal -> 0
    
    # Check mapping log
    assert len(mappings) == 1
    assert mappings[0]['source_id'] == "test_source"
    assert mappings[0]['column'] == 'condition'
    assert len(mappings[0]['mappings']) == 4

def test_normalize_columns_variant_names():
    data = {
        'Donation': [10.5, 12.0],
        'condition': ['ignored', 'control'],
        'randomized': ['yes', 'no']
    }
    df = pd.DataFrame(data)
    logger = logging.getLogger("test")
    
    df_norm, _ = normalize_columns(df, "test", logger)
    
    assert 'donation' not in df_norm.columns
    assert 'prosocial_amount' in df_norm.columns
    assert df_norm['prosocial_amount'].iloc[0] == 10.5
