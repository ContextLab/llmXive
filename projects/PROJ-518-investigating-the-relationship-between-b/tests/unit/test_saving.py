"""
Unit tests for the saving module (T030).
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

from analysis.saving import save_permutation_results, save_sensitivity_summary, save_fwe_corrected_results

def test_save_permutation_results():
    """Test that permutation results are saved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_permutation.csv")
        
        p_values = [0.01, 0.05, 0.10]
        max_stats = [2.5, 1.8, 1.2]
        
        result_path = save_permutation_results(p_values, max_stats, output_path)
        
        assert result_path.exists()
        df = pd.read_csv(result_path)
        
        assert 'p_value' in df.columns
        assert 'max_stat' in df.columns
        assert len(df) == 3
        assert df['p_value'].tolist() == p_values
        assert df['max_stat'].tolist() == max_stats

def test_save_permutation_results_empty_list():
    """Test that empty lists raise ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_permutation.csv")
        
        with pytest.raises(ValueError):
            save_permutation_results([], [], output_path)

def test_save_permutation_results_mismatched_lengths():
    """Test that mismatched list lengths raise ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_permutation.csv")
        
        with pytest.raises(ValueError):
            save_permutation_results([0.01, 0.05], [2.5], output_path)

def test_save_sensitivity_summary():
    """Test that sensitivity summary is saved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_sensitivity.csv")
        
        sensitivity_df = pd.DataFrame({
            'window_length': [20, 30, 40],
            'correlation': [0.45, 0.42, 0.38],
            'p_value': [0.03, 0.05, 0.08]
        })
        
        result_path = save_sensitivity_summary(sensitivity_df, output_path)
        
        assert result_path.exists()
        df = pd.read_csv(result_path)
        
        assert 'window_length' in df.columns
        assert 'correlation' in df.columns
        assert 'p_value' in df.columns
        assert len(df) == 3

def test_save_sensitivity_summary_missing_columns():
    """Test that missing columns raise ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_sensitivity.csv")
        
        sensitivity_df = pd.DataFrame({
            'window_length': [20, 30, 40],
            'correlation': [0.45, 0.42, 0.38]
            # Missing 'p_value'
        })
        
        with pytest.raises(ValueError):
            save_sensitivity_summary(sensitivity_df, output_path)

def test_save_fwe_corrected_results():
    """Test that FWE-corrected results are saved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_fwe.csv")
        
        original_p = [0.01, 0.05, 0.10]
        adjusted_p = [0.03, 0.15, 0.30]
        method = 'max-t'
        
        result_path = save_fwe_corrected_results(adjusted_p, original_p, method, output_path)
        
        assert result_path.exists()
        df = pd.read_csv(result_path)
        
        assert 'original_p_value' in df.columns
        assert 'adjusted_p_value' in df.columns
        assert 'correction_method' in df.columns
        assert len(df) == 3
        assert df['correction_method'].unique()[0] == method
