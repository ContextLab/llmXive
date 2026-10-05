import pytest
import pandas as pd
import os

def test_fdr_correction_logic():
    """
    Integration test for FDR correction logic.
    """
    output_path = "data/processed/correlation_results.csv"
    
    if not os.path.exists(output_path):
        pytest.skip("Output not generated. Run code/03_correlation_analysis.py first.")
    
    df = pd.read_csv(output_path)
    
    # Verify adj_p_value is calculated
    assert 'adj_p_value' in df.columns
    
    # Verify significant flag logic
    sig_df = df[df['significant'] == True]
    if len(sig_df) > 0:
        assert (sig_df['adj_p_value'] < 0.05).all(), "Significant rows must have adj_p < 0.05"
