import pytest
import pandas as pd
import os

def test_correlation_output_schema():
    """
    Contract test for correlation output schema.
    Verifies the existence of required columns: rho, p-value, adj-p-value.
    """
    output_path = "data/processed/correlation_results.csv"
    
    if not os.path.exists(output_path):
        pytest.skip("Output file not generated yet. Run code/03_correlation_analysis.py first.")
    
    df = pd.read_csv(output_path)
    
    required_cols = ['genus', 'rho', 'p_value', 'adj_p_value', 'significant', 'interpretation']
    
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    assert df['rho'].dtype in ['float64', 'float32'], "rho must be numeric"
    assert df['adj_p_value'].dtype in ['float64', 'float32'], "adj_p_value must be numeric"
    assert df['interpretation'].iloc[0] == "associational", "interpretation must be 'associational'"
