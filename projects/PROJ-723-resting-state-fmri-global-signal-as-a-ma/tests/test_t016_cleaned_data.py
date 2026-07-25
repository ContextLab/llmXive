"""
Tests for Task T016: Generate cleaned_data.csv.

Verifies that the generated CSV contains the correct columns,
data types, and no missing values.
"""
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils import read_csv

# Mock data generation for testing the output structure
# Since the actual ingestion depends on T009-T015 which might be complex to mock fully,
# we test the structure of the output if the function were to succeed.
# In a real CI, this would run the full pipeline or use a fixture of processed data.

def test_cleaned_data_structure():
    """
    Test that if cleaned_data.csv exists, it has the correct schema.
    """
    output_path = project_root / "data" / "processed" / "cleaned_data.csv"
    
    # If the file doesn't exist, skip this test (assuming pipeline hasn't run yet)
    # In a real test suite, we might force a run or mock the dependencies.
    if not output_path.exists():
        # Attempt to run the script if we are in a local dev environment? 
        # For now, we assert existence as a prerequisite for the schema test.
        # This test is designed to be run AFTER T016.
        assert False, f"Output file {output_path} not found. Run T016 first."

    df = read_csv(output_path)

    # Check required columns
    required_columns = [
        "Subject_ID", 
        "Global_Signal_SD", 
        "MWQ_Score", 
        "Age", 
        "Sex", 
        "Mean_FD", 
        "Mean_DVARS"
    ]

    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    # Check for missing values
    assert not df.isnull().any().any(), "Dataset contains missing values."

    # Check data types (basic sanity)
    assert df["Subject_ID"].dtype == "object" or df["Subject_ID"].dtype.name.startswith("str"), \
        "Subject_ID should be string/object"
    
    numeric_cols = ["Global_Signal_SD", "MWQ_Score", "Age", "Mean_FD", "Mean_DVARS"]
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric"

    # Check specific constraints
    # Global_Signal_SD should be non-negative
    assert (df["Global_Signal_SD"] >= 0).all(), "Global_Signal_SD must be non-negative"
    
    # MWQ_Score should be non-negative
    assert (df["MWQ_Score"] >= 0).all(), "MWQ_Score must be non-negative"
    
    # Sex should be categorical (0/1 or M/F) - assuming numeric 0/1 based on typical BIDS/CSV conventions
    # If it's string, the check below handles it. If numeric:
    if pd.api.types.is_numeric_dtype(df["Sex"]):
        assert df["Sex"].isin([0, 1, 2, 3]).all(), "Sex should be encoded as numeric (0/1/etc)"
    else:
        assert df["Sex"].isin(["M", "F", "Male", "Female"]).all(), "Sex should be M/F"

    print(f"Test passed: {len(df)} rows validated successfully.")

if __name__ == "__main__":
    test_cleaned_data_structure()