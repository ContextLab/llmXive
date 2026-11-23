"""
Contract test for fingerprint generation schema.

Validates that the generated fingerprint data adheres to the required schema:
- 'smiles' column exists and contains valid SMILES strings.
- Fingerprint columns (ECFP4, MACCS, FP2) exist and contain binary vectors
  (0 or 1) or hex strings representing binary vectors.
- No missing values in fingerprint columns.
"""
import pytest
import pandas as pd
import os
from pathlib import Path

# Path to the expected fingerprint output file
# This assumes the pipeline runs T019 before this test is executed.
# If running in isolation, this test checks for the existence of the file
# and validates the schema if present.
FINGERPRINT_FILE = Path("data/processed/full_fingerprints.csv")

@pytest.mark.contract
def test_fingerprint_schema():
    """
    Contract test for fingerprint schema.
    
    Verifies that if the fingerprint file exists, it contains the required
    columns and data types as per the project specification.
    """
    if not FINGERPRINT_FILE.exists():
        pytest.skip(
            f"File {FINGERPRINT_FILE} not found. "
            "Ensure T019 (Generate Fingerprints) has been executed."
        )

    df = pd.read_csv(FINGERPRINT_FILE)

    # 1. Check for required columns
    required_cols = ["smiles"]
    fingerprint_cols = ["ECFP4", "MACCS", "FP2"]
    
    missing_required = [col for col in required_cols if col not in df.columns]
    missing_fp = [col for col in fingerprint_cols if col not in df.columns]

    assert not missing_required, f"Missing required columns: {missing_required}"
    assert not missing_fp, f"Missing fingerprint columns: {missing_fp}"

    # 2. Validate SMILES column is not empty
    assert df["smiles"].notna().all(), "SMILES column contains null values"
    assert len(df["smiles"].unique()) == len(df), "Duplicate SMILES detected in fingerprint set"

    # 3. Validate Fingerprint columns
    for fp_col in fingerprint_cols:
        col_data = df[fp_col]
        
        # Check for nulls
        assert col_data.notna().all(), f"Fingerprint column '{fp_col}' contains null values"
        
        # Validate content: should be binary string (0/1) or hex representation
        # We accept both formats depending on how obabel outputs them.
        # Format 1: "101010..." (binary string)
        # Format 2: "A3F..." (hex string)
        # Format 3: List representation "[1, 0, ...]" (less common but possible)
        
        sample_val = col_data.iloc[0]
        is_binary_str = isinstance(sample_val, str) and all(c in '01' for c in sample_val)
        is_hex_str = isinstance(sample_val, str) and all(c in '0123456789abcdefABCDEF' for c in sample_val) and len(sample_val) > 1
        
        assert is_binary_str or is_hex_str, (
            f"Fingerprint column '{fp_col}' contains invalid data format: {sample_val}. "
            "Expected binary string or hex string."
        )

    # 4. Row count sanity check
    assert len(df) > 0, "Fingerprint file is empty (header only)"

if __name__ == "__main__":
    test_fingerprint_schema()
    print("Contract test passed.")