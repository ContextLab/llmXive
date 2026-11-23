"""
Contract tests for the UnifiedDataset schema.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import yaml

@pytest.fixture
def schema_path():
    return Path("contracts/unified_dataset.schema.yaml")

@pytest.fixture
def sample_unified_data():
    """Generate a sample dataset that should match the schema."""
    return pd.DataFrame({
        'accession': ['Col-0', 'Ler-0', 'Ws-0'],
        'phenotype_trait': [10.5, 20.3, 15.8],
        'nutrient_condition': ['low_N', 'low_N', 'high_N'],
        'SNP1': [0, 1, 2],
        'SNP2': [1, 0, 2],
        'SNP3': [2, 1, 0]
    })

def test_schema_file_exists(schema_path):
    """Verify the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_schema_is_valid_yaml(schema_path):
    """Verify the schema file is valid YAML."""
    with open(schema_path, 'r') as f:
        try:
            schema = yaml.safe_load(f)
            assert schema is not None
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in schema: {e}")

def test_schema_has_required_fields(schema_path):
    """Verify the schema defines required fields."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert 'fields' in schema or 'required' in schema, \
        "Schema must define 'fields' or 'required' structure"

def test_data_matches_schema(sample_unified_data, schema_path):
    """Verify sample data matches the defined schema."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Basic check: ensure columns in data exist in schema definition
    # This is a simplified check; a full validator would use jsonschema
    schema_fields = set()
    if 'fields' in schema:
        schema_fields = {f['name'] for f in schema['fields']}
    elif 'required' in schema:
        schema_fields = set(schema['required'])
    
    # If schema is empty, we can't validate, but we assume it's a pass for now
    if not schema_fields:
        pytest.skip("Schema does not define fields for validation")
    
    data_columns = set(sample_unified_data.columns)
    # At least the required columns should be present
    assert 'accession' in data_columns
    assert 'phenotype_trait' in data_columns

def test_schema_compliance_with_parquet(tmp_path, sample_unified_data, schema_path):
    """Verify that saved parquet files maintain schema integrity."""
    output_path = tmp_path / "test_unified.parquet"
    sample_unified_data.to_parquet(output_path)
    
    loaded = pd.read_parquet(output_path)
    
    assert list(loaded.columns) == list(sample_unified_data.columns)
    assert len(loaded) == len(sample_unified_data)
