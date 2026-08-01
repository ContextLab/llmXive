"""
Contract test for dataset schema validation.
"""

import pytest
import pandas as pd
from pathlib import Path
from utils.schema_validator import validate_dataset, load_schema

# Path to schema (adjust based on project structure)
SCHEMA_PATH = Path("specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml")

@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    return pd.DataFrame({
        'reactants': [['CCO', 'CCO'], ['CC']],
        'reagents': [['H2SO4'], []],
        'product': ['CCOC2H5', 'C2H6'],
        'yield': [80.0, 90.0],
        'reaction_class': ['substitution', 'addition'],
        'combined_ecfp4': [
            [0] * 2048,
            [0] * 2048
        ],
        'combined_maccs': [
            [0] * 167,
            [0] * 167
        ]
    })

def test_dataset_schema_validation(sample_dataset):
    """Test that a valid dataset passes schema validation."""
    schema = load_schema(SCHEMA_PATH)
    result = validate_dataset(sample_dataset, schema)
    assert result['is_valid'] is True
    assert len(result['errors']) == 0

def test_missing_column_fails_validation(sample_dataset):
    """Test that missing required columns fail validation."""
    schema = load_schema(SCHEMA_PATH)
    # Remove a required column
    df_invalid = sample_dataset.drop(columns=['product'])
    result = validate_dataset(df_invalid, schema)
    assert result['is_valid'] is False
    assert any(err['error'] == 'missing' for err in result['errors'])

def test_wrong_type_fails_validation(sample_dataset):
    """Test that wrong column types fail validation."""
    schema = load_schema(SCHEMA_PATH)
    # Change yield to string
    df_invalid = sample_dataset.copy()
    df_invalid['yield'] = df_invalid['yield'].astype(str)
    result = validate_dataset(df_invalid, schema)
    assert result['is_valid'] is False
    assert any(err['error'] == 'type_mismatch' for err in result['errors'])