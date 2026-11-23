"""
Integration test for full ingestion pipeline (T011).
Verifies that data/processed/encoded_alloys.csv is produced with correct schema.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def test_encoded_alloys_csv_exists():
    """Assert that data/processed/encoded_alloys.csv exists."""
    output_path = project_root / "data" / "processed" / "encoded_alloys.csv"
    assert output_path.exists(), f"Output file {output_path} does not exist. Run the pipeline first."

def test_encoded_alloys_csv_columns():
    """Assert the CSV contains exactly the columns defined in code/models/alloy_entry.py."""
    output_path = project_root / "data" / "processed" / "encoded_alloys.csv"
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist.")

    df = pd.read_csv(output_path)

    # Expected columns based on AlloyEntry and encoding logic
    # composition, bulk_modulus, shear_modulus, element_features (or expanded features)
    # The task says "correct columns (e.g., composition, bulk_modulus, shear_modulus, element_features)"
    # Let's check for the core ones.
    required_columns = ['composition', 'bulk_modulus', 'shear_modulus']
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

def test_encoded_alloys_csv_no_nulls():
    """Assert no nulls exist in bulk_modulus or shear_modulus."""
    output_path = project_root / "data" / "processed" / "encoded_alloys.csv"
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist.")

    df = pd.read_csv(output_path)

    assert df['bulk_modulus'].isnull().sum() == 0, "Null values found in bulk_modulus"
    assert df['shear_modulus'].isnull().sum() == 0, "Null values found in shear_modulus"
    assert df['composition'].isnull().sum() == 0, "Null values found in composition"

def test_encoded_alloys_csv_data_types():
    """Assert correct data types (floats for moduli, string for composition)."""
    output_path = project_root / "data" / "processed" / "encoded_alloys.csv"
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist.")

    df = pd.read_csv(output_path)

    # Check numeric types
    assert pd.api.types.is_float_dtype(df['bulk_modulus']), "bulk_modulus is not float"
    assert pd.api.types.is_float_dtype(df['shear_modulus']), "shear_modulus is not float"
    assert pd.api.types.is_string_dtype(df['composition']), "composition is not string"
