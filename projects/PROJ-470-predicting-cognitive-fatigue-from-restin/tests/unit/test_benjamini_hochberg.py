"""Tests for Benjamini-Hochberg correction task (T022)."""
import os
import csv
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Ensure the code directory is in the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

def test_bh_correction_exists():
    """Assert that bh_corrected_pvalues.csv is created after running the script."""
    # Create a dummy correlation_results.csv for testing
    input_file = "data/analysis/correlation_results.csv"
    output_file = "data/analysis/bh_corrected_pvalues.csv"

    # Ensure directory exists
    os.makedirs("data/analysis", exist_ok=True)

    # Create dummy data with p-values
    dummy_data = [
        {"channel": "Cz", "p_value": 0.01},
        {"channel": "Pz", "p_value": 0.04},
        {"channel": "Fz", "p_value": 0.06},
        {"channel": "Oz", "p_value": 0.001},
        {"channel": "P3", "p_value": 0.15}
    ]

    # Write dummy input
    df_input = pd.DataFrame(dummy_data)
    df_input.to_csv(input_file, index=False)

    # Run the BH correction
    try:
        from benjamini_hochberg import run_benjamini_hochberg
        run_benjamini_hochberg(input_file, output_file)
    except Exception as e:
        pytest.fail(f"Failed to run BH correction: {e}")

    # Assert output file exists
    assert os.path.exists(output_file), f"Output file {output_file} was not created."

    # Load and verify content
    df_output = pd.read_csv(output_file)

    # Check required columns
    required_cols = ['channel', 'p_value', 'p_corrected', 'significant_bh']
    for col in required_cols:
        assert col in df_output.columns, f"Missing required column: {col}"

    # Check that p_corrected is numeric and within [0, 1]
    assert all(df_output['p_corrected'].notna()), "Some p_corrected values are NaN."
    assert all((df_output['p_corrected'] >= 0) & (df_output['p_corrected'] <= 1)), "p_corrected values out of range [0, 1]."

    # Check that significant_bh is boolean
    assert all(df_output['significant_bh'].isin([True, False])), "significant_bh contains non-boolean values."

    # Clean up
    os.remove(input_file)
    os.remove(output_file)

def test_bh_correction_logic():
    """Verify that BH correction logic is applied correctly."""
    # Create a simple dataset where we know the expected outcome
    input_file = "data/analysis/test_correlation.csv"
    output_file = "data/analysis/test_bh_output.csv"
    os.makedirs("data/analysis", exist_ok=True)

    # P-values: [0.01, 0.02, 0.03, 0.04, 0.05] (sorted)
    # m=5, alpha=0.05
    # BH thresholds: (i/m)*alpha -> [0.01, 0.02, 0.03, 0.04, 0.05]
    # Sorted p-values: 0.01, 0.02, 0.03, 0.04, 0.05
    # All p <= threshold -> all significant?
    # Actually, BH finds largest k where p(k) <= (k/m)*alpha
    # Here:
    # i=1: 0.01 <= 0.01 -> ok
    # i=2: 0.02 <= 0.02 -> ok
    # i=3: 0.03 <= 0.03 -> ok
    # i=4: 0.04 <= 0.04 -> ok
    # i=5: 0.05 <= 0.05 -> ok
    # So all should be significant.

    dummy_data = [
        {"channel": "C1", "p_value": 0.01},
        {"channel": "C2", "p_value": 0.02},
        {"channel": "C3", "p_value": 0.03},
        {"channel": "C4", "p_value": 0.04},
        {"channel": "C5", "p_value": 0.05}
    ]

    df_input = pd.DataFrame(dummy_data)
    df_input.to_csv(input_file, index=False)

    from benjamini_hochberg import run_benjamini_hochberg
    df_output = run_benjamini_hochberg(input_file, output_file, alpha=0.05)

    # All should be significant
    assert df_output['significant_bh'].all(), "Not all p-values were marked significant as expected."

    # Clean up
    os.remove(input_file)
    os.remove(output_file)
