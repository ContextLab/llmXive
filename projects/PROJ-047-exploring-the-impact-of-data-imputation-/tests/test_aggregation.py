import os
import json
import tempfile
import pandas as pd
import numpy as np
from analysis.aggregation import compute_run_id, load_run_results, calculate_coverage_rate, aggregate_results, save_summary_dataframe

def test_compute_run_id():
    """Test run ID computation."""
    run_id = compute_run_id(42, 0.5)
    assert isinstance(run_id, str)
    assert len(run_id) == 64  # SHA-256 hash length
    assert run_id == compute_run_id(42, 0.5)  # Deterministic

def test_calculate_coverage_rate():
    """Test coverage rate calculation."""
    estimates = [
        {'ci_lower': 0.4, 'ci_upper': 0.6},
        {'ci_lower': 0.3, 'ci_upper': 0.5},
        {'ci_lower': 0.6, 'ci_upper': 0.8}
    ]
    
    coverage = calculate_coverage_rate(estimates, 0.5)
    assert coverage == 2/3  # 2 out of 3 contain 0.5

def test_aggregate_results():
    """Test aggregation of run results."""
    run_results = [
        {
            'seed': 42,
            'beta': 0.5,
            'ground_truth_ate': 0.5,
            'results': [
                {'method': 'mean', 'estimator': 'ipw', 'ate': 0.6, 'status': 'success', 'coverage_rate': 0.9},
                {'method': 'knn', 'estimator': 'psm', 'ate': 0.55, 'status': 'success', 'coverage_rate': 0.85}
            ]
        }
    ]
    
    df = aggregate_results(run_results)
    
    assert len(df) == 2
    assert df['beta'].iloc[0] == 0.5
    assert df['method'].iloc[0] == 'mean'
    assert df['method'].iloc[1] == 'knn'

def test_save_summary_dataframe():
    """Test saving summary dataframe."""
    df = pd.DataFrame({
        'beta': [0.0, 0.5],
        'method': ['mean', 'knn'],
        'ate': [0.5, 0.6]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        save_summary_dataframe(df, temp_path)
        assert os.path.exists(temp_path)
        
        # Verify content
        loaded_df = pd.read_csv(temp_path)
        assert len(loaded_df) == 2
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
