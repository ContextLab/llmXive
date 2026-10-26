"""
Contract test for the descriptor matrix artifact.
Verifies that data/processed/descriptors.parquet exists and conforms
to the expected schema defined in validators.py.
"""
import pytest
import pandas as pd
from tests.contract.validators import (
    DescriptorMatrix, 
    validate_descriptor_frame, 
    DESCRIPTORS_PARQUET
)

def test_descriptors_parquet_schema():
    """
    Validate that the descriptors parquet file exists and matches 
    the required columns and types.
    """
    # 1. Check existence
    if not DESCRIPTORS_PARQUET.exists():
        pytest.fail(f"Required artifact missing: {DESCRIPTORS_PARQUET}")

    # 2. Load data
    df = pd.read_parquet(DESCRIPTORS_PARQUET)

    # 3. Validate frame structure (metadata + expected descriptors from JSON)
    # This will raise ValueError if columns are missing
    validate_descriptor_frame(df)

    # 4. Validate data types for a sample of rows using Pydantic
    # We check the first and last row to ensure consistency
    for idx in [0, len(df) - 1]:
        row_dict = df.iloc[idx].to_dict()
        try:
            DescriptorMatrix(**row_dict)
        except Exception as e:
            pytest.fail(f"Row {idx} failed Pydantic validation: {e}")

def test_descriptors_no_empty_columns():
    """
    Ensure that no descriptor columns are entirely NaN.
    """
    if not DESCRIPTORS_PARQUET.exists():
        pytest.skip("Artifact missing, skipping content check")
    
    df = pd.read_parquet(DESCRIPTORS_PARQUET)
    descriptor_cols = [c for c in df.columns if c not in {"smiles", "target", "stereochemistry_flag", "flexible_flag"}]
    
    for col in descriptor_cols:
        if df[col].isna().all():
            pytest.fail(f"Column {col} is entirely NaN")
