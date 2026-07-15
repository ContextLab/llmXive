"""
Unit tests for the statistical results generation script.
"""
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Mock the Paths config if needed, or assume it's set up in conftest
# For now, we'll create temporary files for testing.

def test_load_execution_traces():
    """Test loading of execution traces."""
    from analysis.generate_statistical_results import load_execution_traces
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        df_test = pd.DataFrame({
            'architecture': ['dual_track', 'monolithic', 'dual_track'],
            'constraint_count': [5, 6, 7],
            'violation': [0, 1, 0],
            'task_id': ['t1', 't2', 't3']
        })
        df_test.to_csv(f.name, index=False)
        
        loaded_df = load_execution_traces(Path(f.name))
        assert len(loaded_df) == 3
        assert 'violation' in loaded_df.columns
        assert loaded_df['violation'].dtype == int
        
        os.unlink(f.name)

def test_prepare_data_for_glmm():
    """Test data preparation for GLMM."""
    from analysis.generate_statistical_results import prepare_data_for_glmm
    
    df = pd.DataFrame({
        'architecture': ['dual_track', 'monolithic', 'dual_track'],
        'constraint_count': [5.0, 6.0, 7.0],  # Floats
        'violation': [0.0, 1.0, 0.0],  # Floats
        'task_id': ['t1', 't2', 't3']
    })
    
    prepared = prepare_data_for_glmm(df)
    assert prepared['violation'].dtype == int
    assert prepared['constraint_count'].dtype == int

def test_fit_glmm_basic():
    """Test GLMM fitting with basic data."""
    from analysis.generate_statistical_results import fit_glmm
    
    df = pd.DataFrame({
        'architecture': ['dual_track', 'monolithic', 'dual_track', 'monolithic'] * 10,
        'constraint_count': [5, 5, 6, 6] * 10,
        'violation': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        'task_id': [f't{i%40}' for i in range(40)]
    })
    
    result = fit_glmm(df)
    assert 'converged' in result
    assert 'coefficients' in result
    assert 'p_values' in result
    assert 'interaction_p_value' in result
    assert result['converged'] is True  # Should converge on this synthetic data

def test_run_statistical_analysis_integration():
    """Integration test for the full pipeline."""
    from analysis.generate_statistical_results import run_statistical_analysis
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "traces.csv"
        output_path = Path(tmpdir) / "results.json"
        
        df_test = pd.DataFrame({
            'architecture': ['dual_track', 'monolithic', 'dual_track', 'monolithic'] * 20,
            'constraint_count': [5, 5, 6, 6] * 20,
            'violation': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            'task_id': [f't{i}' for i in range(80)]
        })
        df_test.to_csv(input_path, index=False)
        
        result = run_statistical_analysis(input_path, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            saved_data = json.load(f)
        
        assert 'model_summary' in saved_data
        assert 'interaction_p_value' in saved_data['model_summary']
        assert 'effect_sizes' in saved_data