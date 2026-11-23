"""
Unit tests for sensitivity analysis functionality (T038).
"""
import pytest
import pandas as pd
import numpy as np
from code.analysis.sensitivity import sensitivity_rejection_threshold, run_sensitivity_analysis_script
import json
import os
import tempfile

def create_test_dataframe(missing_rate: float = 0.0):
    """Helper to create a test DataFrame with optional missing values."""
    n_rows = 100
    data = {
        'metabolite_A': np.random.rand(n_rows),
        'metabolite_B': np.random.rand(n_rows),
        'metabolite_C': np.random.rand(n_rows),
        'recovery_index': np.random.rand(n_rows)
    }
    df = pd.DataFrame(data)
    
    if missing_rate > 0:
        # Introduce missing values
        total_cells = df.shape[0] * (df.shape[1] - 1) # Exclude target
        n_missing = int(total_cells * missing_rate)
        indices = np.random.choice(df.index, n_missing, replace=False)
        cols = ['metabolite_A', 'metabolite_B', 'metabolite_C']
        for idx in indices:
            col = np.random.choice(cols)
            df.loc[idx, col] = np.nan
    
    return df

def test_sensitivity_all_accepted():
    """Test case where all thresholds accept the data (low missing rate)."""
    df = create_test_dataframe(missing_rate=0.02) # 2% missing
    
    results = sensitivity_rejection_threshold(df, thresholds=[0.08, 0.10, 0.12])
    
    assert len(results['results']) == 3
    assert all(r['accepted'] for r in results['results'])
    assert all(r['r2'] is not None for r in results['results'])
    assert results['summary']['accepted_count'] == 3

def test_sensitivity_partial_rejection():
    """Test case where some thresholds reject the data."""
    df = create_test_dataframe(missing_rate=0.09) # 9% missing
    
    results = sensitivity_rejection_threshold(df, thresholds=[0.08, 0.10, 0.12])
    
    # 0.08 should reject, 0.10 and 0.12 should accept
    assert not results['results'][0]['accepted'] # 0.08
    assert results['results'][1]['accepted']     # 0.10
    assert results['results'][2]['accepted']     # 0.12
    assert results['summary']['accepted_count'] == 2

def test_sensitivity_all_rejected():
    """Test case where all thresholds reject the data (high missing rate)."""
    df = create_test_dataframe(missing_rate=0.15) # 15% missing
    
    results = sensitivity_rejection_threshold(df, thresholds=[0.08, 0.10, 0.12])
    
    assert all(not r['accepted'] for r in results['results'])
    assert results['summary']['accepted_count'] == 0
    assert results['summary']['robustness_score'] == 0.0

def test_sensitivity_invalid_target():
    """Test that an error is raised if target column is missing."""
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    
    with pytest.raises(ValueError, match="Target column"):
        sensitivity_rejection_threshold(df, target_col='nonexistent')

def test_run_sensitivity_analysis_script():
    """Test the script entry point with file I/O."""
    df = create_test_dataframe(missing_rate=0.05)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'test_data.csv')
        output_path = os.path.join(tmpdir, 'results.json')
        
        df.to_csv(input_path, index=False)
        
        run_sensitivity_analysis_script(input_path, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'results' in data
        assert 'summary' in data
        assert len(data['results']) == 3
