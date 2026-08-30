"""
Unit tests for T020c: FDR Correction.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.models.metrics import apply_fdr_correction

def test_fdr_correction_basic():
    """Test basic FDR correction functionality."""
    # Create a temporary input file
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "max_t_stats.csv")
        output_path = os.path.join(tmpdir, "permutation_results.csv")
        
        # Create dummy data
        data = {
            'dimension': ['dim_A', 'dim_B', 'dim_C', 'dim_D'],
            'raw_p': [0.01, 0.04, 0.15, 0.20]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        # Run correction
        result = apply_fdr_correction(input_path, output_path)
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Verify result columns
        assert 'dimension' in result.columns
        assert 'raw_p' in result.columns
        assert 'adjusted_p' in result.columns
        
        # Verify adjusted p-values are >= raw p-values (monotonicity of BH)
        # Note: BH ensures adjusted_p >= raw_p
        assert all(result['adjusted_p'] >= result['raw_p'])
        
        # Verify adjusted p-values are <= 1.0
        assert all(result['adjusted_p'] <= 1.0)
        
        # Verify dimensions match
        assert list(result['dimension']) == ['dim_A', 'dim_B', 'dim_C', 'dim_D']

def test_fdr_correction_single():
    """Test FDR correction with a single dimension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "max_t_stats.csv")
        output_path = os.path.join(tmpdir, "permutation_results.csv")
        
        data = {
            'dimension': ['dim_A'],
            'raw_p': [0.05]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        result = apply_fdr_correction(input_path, output_path)
        
        assert len(result) == 1
        assert result['adjusted_p'].iloc[0] == 0.05  # For n=1, BH p_adj = p_raw

def test_fdr_correction_missing_input():
    """Test that missing input file raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "nonexistent.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        with pytest.raises(FileNotFoundError):
            apply_fdr_correction(input_path, output_path)

def test_fdr_correction_missing_column():
    """Test that missing required column raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "max_t_stats.csv")
        output_path = os.path.join(tmpdir, "permutation_results.csv")
        
        # Missing 'raw_p'
        data = {
            'dimension': ['dim_A'],
            'p_value': [0.05]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError):
            apply_fdr_correction(input_path, output_path)