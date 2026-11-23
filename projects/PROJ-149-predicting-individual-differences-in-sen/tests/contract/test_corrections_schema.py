"""
Contract test for T021: correlations_corrected.csv schema validation.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Import config to resolve paths
try:
    from config import get_path
except ImportError:
    # Fallback if running outside project root context
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
    from config import get_path

CORRECTED_PATH = get_path('processed', 'correlations_corrected.csv')

REQUIRED_COLUMNS = [
    'band',
    'r_value',
    'p_value',
    'n',
    'p_bonferroni',
    'significant'
]

def test_corrections_file_exists():
    """Verify that the corrected correlations file exists."""
    assert os.path.exists(CORRECTED_PATH), f"File not found: {CORRECTED_PATH}"

def test_corrections_schema():
    """Verify the schema of correlations_corrected.csv matches requirements."""
    if not os.path.exists(CORRECTED_PATH):
        pytest.skip("File not generated yet (T021 not run).")
        
    df = pd.read_csv(CORRECTED_PATH)
    
    # Check columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing columns in {CORRECTED_PATH}: {missing_cols}"
    
    # Check data types for new columns
    assert df['p_bonferroni'].dtype in ['float64', 'float32'], "p_bonferroni must be numeric"
    assert df['significant'].dtype == 'bool', "significant must be boolean"
    
    # Check logical consistency: significant should be True iff p_value < (0.05/6)
    threshold = 0.05 / 6
    expected_significant = df['p_value'] < threshold
    assert all(df['significant'] == expected_significant), "Significance flag logic mismatch"
    
    # Check p_bonferroni capping
    assert all(df['p_bonferroni'] <= 1.0), "Adjusted p-values must be <= 1.0"

def test_corrections_content():
    """Basic content validation."""
    if not os.path.exists(CORRECTED_PATH):
        pytest.skip("File not generated yet.")
        
    df = pd.read_csv(CORRECTED_PATH)
    assert len(df) > 0, "Corrections file is empty"
    assert df['n'].min() > 0, "Sample size 'n' must be positive"