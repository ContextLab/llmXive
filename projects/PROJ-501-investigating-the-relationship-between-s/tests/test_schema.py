"""
Tests for the dataset schema and data integrity.
"""
import os
import yaml
import pandas as pd
import pytest
from pathlib import Path

# Path to the schema file
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
DATA_PATH = Path("data/processed/merged_filtered.csv")

def load_schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_data():
    return pd.read_csv(DATA_PATH)

def test_schema_file_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), "Schema file not found at contracts/dataset.schema.yaml"

def test_data_file_exists():
    """Verify the generated data file exists."""
    assert DATA_PATH.exists(), "Data file not found at data/processed/merged_filtered.csv"

def test_schema_structure():
    """Verify the schema has required keys."""
    schema = load_schema()
    assert "columns" in schema, "Schema missing 'columns' definition"
    assert "column_definitions" in schema, "Schema missing 'column_definitions'"

def test_data_columns_match_schema():
    """Verify data columns match the schema definitions."""
    schema = load_schema()
    df = load_data()
    
    schema_cols = {col['name'] for col in schema['column_definitions']}
    data_cols = set(df.columns)
    
    # All schema columns should be present in data (or vice versa depending on strictness)
    # Here we check that data has at least the required columns from the schema
    required_cols = ['star_id', 'flare_count', 'radius', 'mass', 'semi_major_axis', 'density', 'age']
    for col in required_cols:
        assert col in data_cols, f"Data missing required column: {col}"

def test_data_types():
    """Verify basic data types."""
    df = load_data()
    assert df['flare_count'].dtype in ['int64', 'int32'], "flare_count should be integer"
    assert df['mass'].dtype in ['float64', 'float32'], "mass should be float"
    assert df['radius'].dtype in ['float64', 'float32'], "radius should be float"
    assert df['semi_major_axis'].dtype in ['float64', 'float32'], "semi_major_axis should be float"

def test_filtering_logic():
    """Verify that flare_count >= 10 and age is not null."""
    df = load_data()
    assert (df['flare_count'] >= 10).all(), "All records must have flare_count >= 10"
    assert not df['age'].isnull().any(), "Age should be imputed and not null"

def test_schema_constraints():
    """Verify constraints defined in schema are met."""
    schema = load_schema()
    df = load_data()
    
    # Check min_flare_count constraint from schema
    min_flare = schema['constraints']['min_flare_count']
    assert df['flare_count'].min() >= min_flare, f"Minimum flare count {df['flare_count'].min()} < {min_flare}"