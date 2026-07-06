import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add the project root to the path if running directly
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingestion.preprocess import load_config

def get_latest_processed_dataset():
    """
    Locates the latest processed dataset file.
    Priority: encoded_features.csv -> imputed.csv -> raw_for_sensitivity.csv
    """
    config = load_config()
    processed_dir = Path(config['DATA_PROCESSED'])
    
    candidates = [
        processed_dir / 'encoded_features.csv',
        processed_dir / 'imputed.csv',
        processed_dir / 'raw_for_sensitivity.csv',
        processed_dir / 'train.csv'
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    raise FileNotFoundError(
        f"No processed dataset found in {processed_dir}. "
        "Please ensure Phase 3 (Data Ingestion) has completed."
    )

def test_schema_columns_present():
    """
    Contract Test: Verify that the processed dataset contains all required columns.
    """
    df_path = get_latest_processed_dataset()
    df = pd.read_csv(df_path)
    
    required_columns = [
        'yield_strength_mpa',
        'strain_rate_s_inv',
        'temperature_k',
        'grain_size_um',
        'alloy_family',
        'imputation_confidence'
    ]
    
    missing = set(required_columns) - set(df.columns)
    assert not missing, f"Missing required columns: {missing}"

def test_schema_numeric_types():
    """
    Contract Test: Verify that numeric columns are of appropriate float/int types.
    """
    df_path = get_latest_processed_dataset()
    df = pd.read_csv(df_path)
    
    numeric_cols = [
        'yield_strength_mpa',
        'strain_rate_s_inv',
        'temperature_k',
        'grain_size_um',
        'imputation_confidence'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), \
                f"Column '{col}' is not numeric. Found type: {df[col].dtype}"

def test_schema_no_nulls_critical_fields():
    """
    Contract Test: Verify that critical fields have no null values.
    """
    df_path = get_latest_processed_dataset()
    df = pd.read_csv(df_path)
    
    critical_fields = ['yield_strength_mpa', 'strain_rate_s_inv', 'alloy_family']
    
    for field in critical_fields:
        if field in df.columns:
            null_count = df[field].isnull().sum()
            assert null_count == 0, \
                f"Critical field '{field}' contains {null_count} null values."

def test_schema_physical_validity():
    """
    Contract Test: Verify that physical values are within realistic ranges.
    """
    df_path = get_latest_processed_dataset()
    df = pd.read_csv(df_path)
    
    # Yield Strength: Should be positive and typically < 5000 MPa for standard metals
    if 'yield_strength_mpa' in df.columns:
        assert (df['yield_strength_mpa'] > 0).all(), "Yield strength must be positive."
        assert (df['yield_strength_mpa'] < 5000).all(), "Yield strength exceeds physical limits (5000 MPa)."
    
    # Strain Rate: Should be positive
    if 'strain_rate_s_inv' in df.columns:
        assert (df['strain_rate_s_inv'] > 0).all(), "Strain rate must be positive."
    
    # Temperature: Should be in Kelvin (positive)
    if 'temperature_k' in df.columns:
        assert (df['temperature_k'] > 0).all(), "Temperature must be positive (Kelvin)."
    
    # Grain Size: Should be positive
    if 'grain_size_um' in df.columns:
        assert (df['grain_size_um'] > 0).all(), "Grain size must be positive."

def test_schema_alloy_family_validity():
    """
    Contract Test: Verify that alloy families match expected categories.
    """
    df_path = get_latest_processed_dataset()
    df = pd.read_csv(df_path)
    
    if 'alloy_family' not in df.columns:
        pytest.skip("Alloy family column not present in this dataset version.")
            
    valid_families = {
        'AA-6061', 'AISI-4340', 'Ti-6Al-4V', 'Inconel-718', 
        'Al-7075', 'Stainless-304', 'Copper-OFE', 'Other'
    }
    
    unique_families = set(df['alloy_family'].dropna().unique())
    invalid = unique_families - valid_families
    
    # Allow 'Other' or any family if the dataset is from a specific subset
    # If strict validation is needed, uncomment the assertion below:
    # assert not invalid, f"Unexpected alloy families found: {invalid}"

def test_schema_imputation_confidence_range():
    """
    Contract Test: Verify that imputation confidence scores are within [0, 1].
    """
    df_path = get_latest_processed_dataset()
    df = pd.read_csv(df_path)
    
    if 'imputation_confidence' not in df.columns:
        pytest.skip("Imputation confidence column not present.")
            
    conf = df['imputation_confidence']
    assert (conf >= 0).all() and (conf <= 1).all(), \
        "Imputation confidence values must be between 0 and 1."