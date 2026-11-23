"""
Unit tests for the Benjamini-Hochberg correction implementation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from bh_correction import apply_benjamini_hochberg, run_bh_correction, load_results

def test_apply_bh_monotonicity():
    """Test that adjusted p-values are monotonically increasing when sorted by raw p-value."""
    # Create a set of p-values that are not monotonic in their raw form
    p_values = pd.Series([0.1, 0.01, 0.05, 0.001, 0.02])
    
    adjusted = apply_benjamini_hochberg(p_values)
    
    # Sort the adjusted values by the original p-values
    sorted_indices = p_values.argsort()
    sorted_adjusted = adjusted.iloc[sorted_indices]
    
    # Check monotonicity
    assert sorted_adjusted.is_monotonic_increasing, "Adjusted p-values must be monotonically increasing"

def test_apply_bh_bounds():
    """Test that adjusted p-values are between 0 and 1."""
    p_values = pd.Series([0.001, 0.5, 0.99])
    adjusted = apply_benjamini_hochberg(p_values)
    
    assert (adjusted >= 0).all(), "Adjusted p-values cannot be negative"
    assert (adjusted <= 1).all(), "Adjusted p-values cannot exceed 1"

def test_apply_bh_identity():
    """Test that if all p-values are 1, adjusted values are 1."""
    p_values = pd.Series([1.0, 1.0, 1.0])
    adjusted = apply_benjamini_hochberg(p_values)
    assert (adjusted == 1.0).all()

def test_run_bh_correction_file_io():
    """Test the full file I/O pipeline of run_bh_correction."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("resolution,class_id,p_value\n")
        f.write("30m,forest,0.01\n")
        f.write("30m,urban,0.04\n")
        f.write("60m,forest,0.06\n")
        f.write("60m,urban,0.15\n")
        temp_path = f.name

    try:
        output_path = Path(temp_path.replace('.csv', '_adj.csv'))
        result_path = run_bh_correction(Path(temp_path), output_path)
        
        # Verify file exists
        assert result_path.exists(), "Output file was not created"
        
        # Verify content
        df = pd.read_csv(result_path)
        assert 'p_value_adj' in df.columns, "p_value_adj column missing"
        assert 'is_significant_adj' in df.columns, "is_significant_adj column missing"
        assert len(df) == 4, "Row count mismatch"
        
        # Verify values are numeric
        assert pd.api.types.is_numeric_dtype(df['p_value_adj']), "p_value_adj is not numeric"
        
        # Cleanup
        os.remove(result_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_run_bh_correction_overwrite():
    """Test that run_bh_correction can overwrite the input file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("resolution,class_id,p_value\n")
        f.write("30m,forest,0.01\n")
        temp_path = f.name

    try:
        # Call with output_path=None (default behavior: overwrite)
        result_path = run_bh_correction(Path(temp_path), output_path=None)
        
        assert result_path == Path(temp_path), "Result path should be the input path"
        assert result_path.exists(), "File was overwritten but does not exist"
        
        df = pd.read_csv(result_path)
        assert 'p_value_adj' in df.columns
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
