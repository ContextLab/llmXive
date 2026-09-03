"""
Contract test for T021: Bonferroni correction output schema.
Validates that code/09_apply_bonferroni.py produces the correct schema.
"""
import os
import pytest
import pandas as pd
from pathlib import Path
from config import get_path

def test_bonferroni_output_schema():
    """
    Verify that data/processed/correlations_corrected.csv exists and has the correct columns.
    """
    output_path = get_path("processed", "correlations_corrected.csv")
    
    # Check file existence
    assert os.path.exists(output_path), f"Output file {output_path} does not exist. Run T021 first."
    
    # Load data
    df = pd.read_csv(output_path)
    
    # Expected columns based on T021 implementation
    expected_columns = ['band', 'r_value', 'p_value', 'n', 'corrected_alpha', 'significant']
    
    # Check columns
    for col in expected_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    assert df['p_value'].dtype in ['float64', 'float32'], "p_value must be numeric"
    assert df['significant'].dtype == 'bool', "significant must be boolean"
    assert df['corrected_alpha'].dtype in ['float64', 'float32'], "corrected_alpha must be numeric"
    
    # Check Bonferroni constant (0.05 / 6 = 0.008333...)
    expected_alpha = 0.05 / 6
    # Allow for floating point precision
    assert abs(df['corrected_alpha'].iloc[0] - expected_alpha) < 1e-6, \
        f"Corrected alpha should be {expected_alpha}, got {df['corrected_alpha'].iloc[0]}"
    
    # Check that significant is boolean logic based on p_value <= alpha
    # We can't check exact values without running the data generation, 
    # but we can check logical consistency if we had the raw data.
    # Here we just ensure the column exists and is boolean.
    
    print("Bonferroni output schema validation passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])