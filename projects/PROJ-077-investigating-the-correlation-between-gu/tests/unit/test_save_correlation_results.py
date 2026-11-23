import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from save_correlation_results import save_correlation_results

def test_save_correlation_results_creates_file():
    """Test that save_correlation_results creates the output CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_correlation_results.csv'
        
        r_value = 0.45
        p_value = 0.023
        n_obs = 1500

        save_correlation_results(r_value, p_value, n_obs, output_path)

        assert output_path.exists(), "Output CSV file was not created"

        df = pd.read_csv(output_path)
        assert len(df) == 1, "Expected exactly one row in results"
        assert 'r_value' in df.columns, "Missing r_value column"
        assert 'p_value' in df.columns, "Missing p_value column"
        assert 'n_obs' in df.columns, "Missing n_obs column"
        
        assert abs(df['r_value'].iloc[0] - r_value) < 1e-6, "r_value mismatch"
        assert abs(df['p_value'].iloc[0] - p_value) < 1e-6, "p_value mismatch"
        assert df['n_obs'].iloc[0] == n_obs, "n_obs mismatch"

def test_save_correlation_results_schema():
    """Test that the output CSV has the exact required schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_correlation_results.csv'
        
        save_correlation_results(0.5, 0.01, 1000, output_path)

        df = pd.read_csv(output_path)
        
        # Check exact column names
        expected_columns = ['r_value', 'p_value', 'n_obs']
        assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"

def test_save_correlation_results_data_types():
    """Test that values are saved as correct types (float, float, int)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_correlation_results.csv'
        
        save_correlation_results(0.123456789, 0.000123, 9999, output_path)

        df = pd.read_csv(output_path)
        
        # Check types (pandas might infer float for int if it looks like one, but n_obs should be numeric)
        assert isinstance(df['r_value'].iloc[0], (float, np.floating)), "r_value should be float"
        assert isinstance(df['p_value'].iloc[0], (float, np.floating)), "p_value should be float"
        assert isinstance(df['n_obs'].iloc[0], (int, np.integer)), "n_obs should be int"