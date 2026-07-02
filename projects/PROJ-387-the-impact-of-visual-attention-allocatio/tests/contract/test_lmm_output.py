"""
Contract test for LMM output schema (T032).
Verifies that the output CSV contains the required columns and data types.
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_output_path

def test_lmm_output_schema():
    """
    Verifies that output/results/lmm_summary.csv exists and has the correct schema.
    Columns: metric, valence, coef, p_raw
    """
    output_path = get_output_path()
    output_file = output_path / "results" / "lmm_summary.csv"

    # Assert file exists
    assert output_file.exists(), f"Output file {output_file} does not exist. Run code/analysis/lmm_model.py first."

    # Load CSV
    df = pd.read_csv(output_file)

    # Assert required columns
    required_columns = ['metric', 'valence', 'coef', 'p_raw']
    missing_cols = [col for col in required_columns if col not in df.columns]
    assert not missing_cols, f"Missing required columns: {missing_cols}"

    # Assert data types (basic check)
    assert df['coef'].dtype in ['float64', 'float32', 'int64'], "coef should be numeric"
    assert df['p_raw'].dtype in ['float64', 'float32', 'int64'], "p_raw should be numeric"

    # Assert no nulls in key columns
    assert not df['metric'].isnull().any(), "metric column contains nulls"
    assert not df['valence'].isnull().any(), "valence column contains nulls"
    assert not df['coef'].isnull().any(), "coef column contains nulls"
    assert not df['p_raw'].isnull().any(), "p_raw column contains nulls"

    # Assert valid range for p-values (0 to 1)
    assert (df['p_raw'] >= 0).all() and (df['p_raw'] <= 1).all(), "p_raw values must be between 0 and 1"

    print("Contract test passed: LMM output schema is valid.")