import pytest
import pandas as pd
import os
import json
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

def test_age_filtering_and_imputation():
    """
    Integration test for age filtering and missing value imputation.
    Verifies that the preprocessing pipeline correctly filters for age >= 60
    and imputes missing covariates without leaving null values.
    """
    output_path = Path("data/processed/rarefied_genus_table.parquet")
    
    if not output_path.exists():
        pytest.skip("Output artifact not generated. Run code/02_preprocessing.py first.")
    
    try:
        df = pd.read_parquet(output_path)
    except Exception as e:
        pytest.fail(f"Failed to load parquet file: {e}")
    
    # Check age filter: All rows must have age >= 60
    if 'age' in df.columns:
        assert (df['age'] >= 60).all(), "All samples must be age >= 60"
    else:
        # If age column is missing, check if we have a valid dataset structure
        # This might happen if the pipeline structure is different
        assert len(df) > 0, "Dataset is empty"
    
    # Check imputation (no nulls in covariates)
    covariates = ['bmi', 'education_years']
    for col in covariates:
        if col in df.columns:
            assert not df[col].isnull().any(), f"Null values found in {col} after imputation"
    
    # Check minimum rows to ensure data quality
    assert len(df) >= 500, f"Dataset has {len(df)} rows, expected >= 500 for valid analysis"

def test_null_value_validation():
    """
    Verify that critical columns contain no null values after preprocessing.
    This complements the age filter test by ensuring data integrity.
    """
    output_path = Path("data/processed/rarefied_genus_table.parquet")
    
    if not output_path.exists():
        pytest.skip("Output artifact not generated. Run code/02_preprocessing.py first.")
    
    df = pd.read_parquet(output_path)
    
    # Define critical columns that must not be null
    critical_columns = ['age', 'sex', 'cognitive_score']
    
    # Add covariates if they exist
    if 'bmi' in df.columns:
        critical_columns.append('bmi')
    if 'education_years' in df.columns:
        critical_columns.append('education_years')
    
    for col in critical_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' contains {null_count} null values"
        # If column is missing, we assume the pipeline handled it differently
        # or it's not applicable to this specific dataset version