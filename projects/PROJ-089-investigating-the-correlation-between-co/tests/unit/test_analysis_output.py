import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import run_analysis, check_vif, calculate_partial_correlations, run_meta_analysis, run_sensitivity_analysis

def test_run_analysis_creates_files():
    """Test that run_analysis creates the required CSV files."""
    # Create a mock unified_metrics.csv
    mock_data = {
        'total_lines_changed': [100, 200, 150, 300, 250, 120, 180, 220],
        'debt_score': [10, 20, 15, 30, 25, 12, 18, 22],
        'avg_loc': [15, 20, 18, 25, 22, 16, 19, 21],
        'repo_id': ['repo1', 'repo1', 'repo1', 'repo2', 'repo2', 'repo2', 'repo2', 'repo2'],
        'contributor_count': [5, 5, 5, 8, 8, 8, 8, 8]
    }
    df = pd.DataFrame(mock_data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, 'unified_metrics.csv')
        output_dir = os.path.join(tmpdir, 'results')
        
        df.to_csv(data_path, index=False)
        
        # Run analysis
        results = run_analysis(data_path, output_dir)
        
        # Verify files exist
        assert os.path.exists(results['correlation_results'])
        assert os.path.exists(results['meta_analysis_results'])
        assert os.path.exists(results['sensitivity_analysis'])
        
        # Verify content is not empty
        corr_df = pd.read_csv(results['correlation_results'])
        assert len(corr_df) > 0
        assert 'value' in corr_df.columns
        assert not corr_df['value'].isna().all()

def test_check_vif():
    """Test VIF calculation."""
    data = {
        'x1': [1, 2, 3, 4, 5],
        'x2': [2, 4, 6, 8, 10], # Perfectly correlated with x1
        'x3': [1, 3, 2, 4, 5]
    }
    df = pd.DataFrame(data)
    vif = check_vif(df, ['x1', 'x2', 'x3'])
    
    assert 'x1' in vif
    assert 'x2' in vif
    assert 'x3' in vif
    # x1 and x2 should have high VIF
    assert vif['x1'] > 5 or vif['x2'] > 5

def test_partial_correlation():
    """Test partial correlation calculation."""
    data = {
        'x': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'y': [2, 4, 5, 4, 5, 7, 8, 8, 9, 10],
        'z': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # Control variable
    }
    df = pd.DataFrame(data)
    r, p = calculate_partial_correlations(df, 'x', 'y', ['z'])
    
    assert not np.isnan(r)
    assert 0 <= p <= 1

def test_meta_analysis():
    """Test meta-analysis function."""
    results = [
        {'repo_id': 'r1', 'r': 0.5, 'n': 100},
        {'repo_id': 'r2', 'r': 0.6, 'n': 150},
        {'repo_id': 'r3', 'r': 0.4, 'n': 80}
    ]
    meta_df = run_meta_analysis(results)
    
    assert not meta_df.empty
    assert 'meta_r' in meta_df.columns
    assert not np.isnan(meta_df['meta_r'].iloc[0])

def test_sensitivity_analysis():
    """Test sensitivity analysis function."""
    data = {
        'total_lines_changed': [100, 200, 150, 300, 250, 120, 180, 220],
        'debt_score': [10, 20, 15, 30, 25, 12, 18, 22],
        'avg_loc': [15, 20, 18, 25, 22, 16, 19, 21]
    }
    df = pd.DataFrame(data)
    thresholds = [5, 10, 20]
    
    sens_df = run_sensitivity_analysis(df, thresholds, 'total_lines_changed', 'debt_score', [])
    
    assert len(sens_df) == len(thresholds)
    assert 'threshold' in sens_df.columns
    assert 'r' in sens_df.columns