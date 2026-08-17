"""
Tests for the energy decay schema (T006b).
Verifies that the generated CSV matches the schema definition.
"""
import os
import yaml
import pandas as pd
import pytest
from pathlib import Path

# Path to the schema file
SCHEMA_PATH = "contracts/energy_schema.schema.yaml"
OUTPUT_PATH = "data/processed/energy_decay.csv"

def load_schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def schema():
    return load_schema()

@pytest.fixture
def df():
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip(f"Output file {OUTPUT_PATH} not found. Run simulation first.")
    return pd.read_csv(OUTPUT_PATH)

def test_schema_exists(schema):
    """Ensure the schema file is valid YAML and contains required keys."""
    assert schema is not None
    assert 'columns' in schema
    assert 'name' in schema

def test_csv_columns_match_schema(df, schema):
    """Verify that the CSV columns match the schema definition."""
    schema_cols = [col['name'] for col in schema['columns']]
    csv_cols = list(df.columns)
    
    assert set(schema_cols) == set(csv_cols), \
        f"Columns mismatch. Schema: {schema_cols}, CSV: {csv_cols}"

def test_graph_id_not_null(df):
    """Check that graph_id is not null."""
    assert df['graph_id'].notnull().all(), "graph_id contains null values"

def test_class_allowed_values(df, schema):
    """Check that 'class' column contains only allowed values."""
    allowed = schema['columns'][1]['constraints']['allowed_values'] # class is 2nd col
    assert df['class'].isin(allowed).all(), f"class contains invalid values: {df[~df['class'].isin(allowed)]['class'].unique()}"

def test_decay_rate_bounds(df, schema):
    """Check decay_rate is within bounds."""
    min_val = schema['columns'][3]['constraints']['min']
    max_val = schema['columns'][3]['constraints']['max']
    assert (df['decay_rate'] >= min_val).all(), f"decay_rate below min {min_val}"
    assert (df['decay_rate'] <= max_val).all(), f"decay_rate above max {max_val}"

def test_r_squared_bounds(df, schema):
    """Check r_squared is between 0 and 1."""
    assert (df['r_squared'] >= 0.0).all(), "r_squared < 0"
    assert (df['r_squared'] <= 1.0).all(), "r_squared > 1"

def test_fit_status_allowed_values(df, schema):
    """Check fit_status allowed values."""
    allowed = schema['columns'][5]['constraints']['allowed_values']
    assert df['fit_status'].isin(allowed).all(), f"fit_status invalid: {df[~df['fit_status'].isin(allowed)]['fit_status'].unique()}"

def test_resonance_flag_boolean(df):
    """Check resonance_flag is boolean."""
    assert df['resonance_flag'].dtype == 'bool', "resonance_flag is not boolean"

def test_exclusion_reason_format(df, schema):
    """Check exclusion_reason format."""
    allowed = schema['columns'][7]['constraints']['allowed_values']
    assert df['exclusion_reason'].isin(allowed).all(), f"exclusion_reason invalid: {df[~df['exclusion_reason'].isin(allowed)]['exclusion_reason'].unique()}"

def test_checksum_format(df, schema):
    """Check checksum is a valid SHA-256 hex string."""
    import re
    pattern = re.compile(r'^[a-f0-9]{64}$')
    assert df['checksum'].str.match(pattern).all(), "checksum format invalid"
