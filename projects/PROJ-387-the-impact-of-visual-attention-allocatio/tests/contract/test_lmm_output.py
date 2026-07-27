"""
Contract test for LMM output schema (T032).
Verifies that the output CSV has the required columns and types.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_project_root

def test_lmm_output_schema():
    """
    Contract test: test_lmm_output_schema
    Verifies the existence and schema of output/results/lmm_summary.csv
    """
    project_root = get_project_root()
    output_file = project_root / "output" / "results" / "lmm_summary.csv"

    # The test expects the file to exist (assuming T020 has run)
    # In a real CI pipeline, this would run after the script.
    # For this unit test, we assert existence and schema.
    
    assert output_file.exists(), f"Output file {output_file} does not exist. Run code/analysis/lmm_model.py first."

    df = pd.read_csv(output_file)

    # Required columns per T020
    required_columns = ['metric', 'valence', 'coef', 'p_raw']
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    # Verify types (basic check)
    assert df['coef'].dtype in ['float64', 'float32'], "coef should be numeric"
    assert df['p_raw'].dtype in ['float64', 'float32'], "p_raw should be numeric"

    # Verify no empty strings in key columns
    assert not df['metric'].isna().any(), "metric column contains NaN"
    assert not df['valence'].isna().any(), "valence column contains NaN"

    # Verify we have at least one result
    assert len(df) > 0, "LMM summary is empty"

    print("LMM Output Schema Contract Test: PASSED")