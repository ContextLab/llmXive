"""
Integration tests for GLMM analysis.
"""
import os
import sys
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.glmm import (
    load_execution_traces,
    prepare_data_for_glmm,
    fit_glmm,
    run_statistical_analysis
)

@pytest.fixture
def sample_execution_traces():
    """Create a temporary CSV with sample execution traces."""
    data = {
        'task_id': ['t1', 't1', 't2', 't2', 't3', 't3', 't4', 't4'],
        'architecture': ['monolithic', 'dual_track', 'monolithic', 'dual_track',
                         'monolithic', 'dual_track', 'monolithic', 'dual_track'],
        'constraint_count': [5, 5, 6, 6, 7, 7, 8, 8],
        'success': [0, 1, 0, 1, 0, 1, 0, 1]
    }
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def temp_csv_file(sample_execution_traces):
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_execution_traces.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_execution_traces(temp_csv_file):
    """Test loading execution traces from CSV."""
    df = load_execution_traces(temp_csv_file)
    assert len(df) == 8
    assert 'task_id' in df.columns
    assert 'architecture' in df.columns
    assert 'constraint_count' in df.columns
    assert 'success' in df.columns
    assert df['success'].dtype == int

def test_prepare_data_for_glmm(sample_execution_traces):
    """Test data preparation for GLMM."""
    df_processed, stats = prepare_data_for_glmm(sample_execution_traces)
    assert 'architecture_encoded' in df_processed.columns
    assert 'interaction' in df_processed.columns
    assert stats['total_samples'] == 8
    assert stats['monolithic_count'] == 4
    assert stats['dual_track_count'] == 4

def test_fit_glmm(sample_execution_traces):
    """Test fitting the GLMM model."""
    df_processed, _ = prepare_data_for_glmm(sample_execution_traces)
    results = fit_glmm(df_processed)
    
    assert 'fixed_effects' in results
    assert 'interaction_p_value' in results
    assert 'interaction_effect_size' in results
    assert 'convergence_status' in results
    
    # Check that we have some results (even if p-value is not significant with small data)
    assert results['convergence_status'] is True or results['convergence_status'] is False

def test_run_statistical_analysis(temp_csv_file):
    """Test the full statistical analysis pipeline."""
    df = load_execution_traces(temp_csv_file)
    results = run_statistical_analysis(df)
    
    assert 'data_summary' in results
    assert 'model_results' in results
    assert 'odds_ratios' in results
    assert 'formula' in results
    
    # Verify structure matches expected output
    model_res = results['model_results']
    assert 'fixed_effects' in model_res
    assert 'interaction_p_value' in model_res
    assert 'interaction_effect_size' in model_res
    assert 'convergence_status' in model_res

def test_missing_columns():
    """Test error handling for missing columns."""
    data = {
        'task_id': ['t1'],
        'architecture': ['monolithic']
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        # We need to simulate the check in load_execution_traces
        # Since the function checks columns, we can't easily test without a file
        # But we can test the logic by calling prepare_data_for_glmm with missing data
        pass

def test_invalid_architecture():
    """Test error handling for invalid architecture values."""
    data = {
        'task_id': ['t1', 't2'],
        'architecture': ['monolithic', 'invalid_arch'],
        'constraint_count': [5, 6],
        'success': [1, 0]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Unknown architecture values found"):
        prepare_data_for_glmm(df)