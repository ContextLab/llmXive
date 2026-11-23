import pytest
import pandas as pd
import yaml
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from preprocess import load_schema, validate_schema

def test_schema_validation_pass(tmp_path):
    """Test validation passes on correct data."""
    schema = {
        'required_columns': ['a', 'b'],
        'types': {'a': 'float', 'b': 'float'}
    }
    schema_path = tmp_path / "schema.yaml"
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    df = pd.DataFrame({'a': [1.0], 'b': [2.0]})
    
    loaded_schema = load_schema(str(schema_path))
    assert validate_schema(df, loaded_schema) is True

def test_schema_validation_fail(tmp_path):
    """Test validation fails on missing column."""
    schema = {
        'required_columns': ['a', 'b'],
        'types': {'a': 'float', 'b': 'float'}
    }
    schema_path = tmp_path / "schema.yaml"
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    df = pd.DataFrame({'a': [1.0]}) # Missing 'b'
    
    loaded_schema = load_schema(str(schema_path))
    with pytest.raises(ValueError, match="Missing required column: b"):
        validate_schema(df, loaded_schema)

def test_cleaned_dataset_contract():
    """
    Contract test: Validate data/processed/cleaned_316L.csv against contracts/dataset.schema.yaml.
    This test expects the file to exist after T014 completes.
    """
    base_dir = Path(__file__).parent.parent.parent
    data_file = base_dir / "data" / "processed" / "cleaned_316L.csv"
    schema_file = base_dir / "contracts" / "dataset.schema.yaml"
    
    if not data_file.exists():
        pytest.skip("cleaned_316L.csv not found. Run T014 first.")
    
    if not schema_file.exists():
        pytest.skip("dataset.schema.yaml not found.")
    
    df = pd.read_csv(data_file)
    schema = load_schema(str(schema_file))
    
    try:
        validate_schema(df, schema)
    except ValueError as e:
        pytest.fail(f"Schema validation failed: {e}")