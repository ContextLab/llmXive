"""
Unit tests for T035: Alpha Sensitivity Analysis.
"""
import pytest
import pandas as pd
import numpy as np
from code.models.metrics import calculate_sensitivity_analysis, run_sensitivity_analysis
from pathlib import Path
import tempfile
import os

def test_calculate_sensitivity_analysis_default_alphas():
    """Test that default alphas are 0.01 to 0.10."""
    p_vals = [0.005, 0.015, 0.025, 0.055, 0.095, 0.15]
    df = calculate_sensitivity_analysis(p_vals)
    
    assert len(df) == 10, "Should have exactly 10 rows"
    
    expected_alphas = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    assert list(df['alpha']) == expected_alphas, "Alpha values should match expected sequence"

def test_calculate_sensitivity_analysis_significance_rate():
    """Test significance rate calculation."""
    # 2 out of 5 p-values are <= 0.02 (0.005, 0.015)
    p_vals = [0.005, 0.015, 0.025, 0.055, 0.10]
    df = calculate_sensitivity_analysis(p_vals, alphas=[0.02, 0.05, 0.10])
    
    # alpha=0.02: 2/5 = 0.4
    row_002 = df[df['alpha'] == 0.02].iloc[0]
    assert abs(row_002['significance_rate'] - 0.4) < 1e-6
    
    # alpha=0.05: 3/5 = 0.6
    row_005 = df[df['alpha'] == 0.05].iloc[0]
    assert abs(row_005['significance_rate'] - 0.6) < 1e-6
    
    # alpha=0.10: 4/5 = 0.8
    row_010 = df[df['alpha'] == 0.10].iloc[0]
    assert abs(row_010['significance_rate'] - 0.8) < 1e-6

def test_run_sensitivity_analysis_output_file():
    """Test that run_sensitivity_analysis writes a CSV file."""
    # Create a mock model results dataframe
    data = {
        'term': ['A', 'B', 'C'],
        'estimate': [1.0, 2.0, 3.0],
        'pvalue': [0.005, 0.025, 0.055]
    }
    df_model = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_sensitivity.csv"
        run_sensitivity_analysis(df_model, p_value_column='pvalue', output_path=output_path)
        
        assert output_path.exists(), "Output file should be created"
        
        df_output = pd.read_csv(output_path)
        assert len(df_output) == 10, "Output should have 10 rows"
        assert 'alpha' in df_output.columns
        assert 'significance_rate' in df_output.columns

def test_empty_p_values():
    """Test handling of empty p-value list."""
    df = calculate_sensitivity_analysis([])
    assert len(df) == 10, "Should still return 10 rows for alphas"
    assert all(df['significance_rate'] == 0.0), "Significance rate should be 0 for empty input"
