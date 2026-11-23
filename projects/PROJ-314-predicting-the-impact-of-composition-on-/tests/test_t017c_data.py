import pandas as pd
import pytest
from pathlib import Path

def test_t017c_dataset_exists_and_valid():
    """
    Verify that T017c created a valid test dataset with exactly 29 rows
    where sample_count >= 30 for all rows.
    """
    data_path = Path("data/raw/test_n29.csv")
    
    # Assert file exists
    assert data_path.exists(), f"File {data_path} does not exist"
    
    # Load the dataset
    df = pd.read_csv(data_path)
    
    # Assert exactly 29 rows
    assert len(df) == 29, f"Expected 29 rows, found {len(df)}"
    
    # Assert required columns exist
    required_cols = ["composition", "weibull_modulus", "sample_count", "sintering_temp", 
                    "primary_anion_cation_group", "is_imputed", "mean_atomic_radius", 
                    "electronegativity_std", "valence_electron_concentration"]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Assert all sample_count values are >= 30
    assert (df["sample_count"] >= 30).all(), "Not all sample_count values are >= 30"
    
    # Assert no missing values in critical columns
    assert df["sample_count"].notna().all(), "Missing values in sample_count column"
    assert df["weibull_modulus"].notna().all(), "Missing values in weibull_modulus column"
    assert df["composition"].notna().all(), "Missing values in composition column"
    
    print(f"✓ T017c dataset verified: {len(df)} rows, all sample_count >= 30")