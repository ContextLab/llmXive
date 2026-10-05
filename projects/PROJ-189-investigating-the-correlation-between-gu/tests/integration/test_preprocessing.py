import pytest
import pandas as pd
import os

def test_age_filtering_and_imputation():
    """
    Integration test for age filtering and missing value imputation.
    """
    output_path = "data/processed/rarefied_genus_table.parquet"
    
    if not os.path.exists(output_path):
        pytest.skip("Output not generated. Run code/02_preprocessing.py first.")
    
    df = pd.read_parquet(output_path)
    
    # Check age filter
    assert (df['age'] >= 60).all(), "All samples must be age >= 60"
    
    # Check imputation (no nulls in covariates)
    covariates = ['bmi', 'education_years']
    for col in covariates:
        if col in df.columns:
            assert not df[col].isnull().any(), f"Null values found in {col}"
    
    # Check minimum rows
    assert len(df) >= 500, f"Dataset has {len(df)} rows, expected >= 500"
