import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_bh_correction import apply_benjamini_hochberg, load_metrics_data, compute_p_values_from_raw_data

def test_apply_benjamini_hochberg_basic():
    """Test basic BH correction functionality."""
    p_values = [0.01, 0.03, 0.04, 0.06, 0.10]
    names = ['m1', 'm2', 'm3', 'm4', 'm5']
    
    result = apply_benjamini_hochberg(p_values, names)
    
    assert len(result) == 5
    assert 'metric' in result.columns
    assert 'raw_p' in result.columns
    assert 'adjusted_p' in result.columns
    assert 'significant' in result.columns
    
    # Check that adjusted p-values are within [0, 1]
    assert all((result['adjusted_p'] >= 0) & (result['adjusted_p'] <= 1))
    
    # Check monotonicity (adjusted_p should be non-decreasing when sorted by raw_p)
    sorted_result = result.sort_values('raw_p')
    adjusted = sorted_result['adjusted_p'].values
    assert all(adjusted[i] <= adjusted[i+1] for i in range(len(adjusted)-1))

def test_apply_benjamini_hochberg_single():
    """Test with a single p-value."""
    p_values = [0.04]
    names = ['m1']
    
    result = apply_benjamini_hochberg(p_values, names)
    assert len(result) == 1
    assert result['adjusted_p'].iloc[0] == 0.04  # n=1, rank=1 -> p * 1/1 = p

def test_apply_benjamini_hochberg_empty():
    """Test with empty input."""
    result = apply_benjamini_hochberg([], [])
    assert len(result) == 0

def test_compute_p_values_from_raw_data():
    """Test p-value computation from synthetic raw data."""
    # Create temporary directory and mock data
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir)
        
        # Create a mock CSV
        data = {
            'snippet_id': [1, 2, 3, 4],
            'group': ['human', 'human', 'llm', 'llm'],
            'score': [10.0, 12.0, 15.0, 18.0]
        }
        df = pd.DataFrame(data)
        csv_path = metrics_dir / "test_metric.csv"
        df.to_csv(csv_path, index=False)
        
        # Load data
        metrics_data = load_metrics_data(metrics_dir)
        assert 'test_metric' in metrics_data
        
        # Compute p-values
        p_values, names = compute_p_values_from_raw_data(metrics_data)
        
        assert len(p_values) == 1
        assert len(names) == 1
        assert names[0] == 'test_metric'
        assert 0 <= p_values[0] <= 1

def test_bh_correction_significance():
    """Test that significance is correctly determined based on adjusted p-values."""
    # Use p-values that will result in some significant and some not
    p_values = [0.001, 0.01, 0.05, 0.20]
    names = ['sig1', 'sig2', 'ns1', 'ns2']
    
    result = apply_benjamini_hochberg(p_values, names)
    
    # With alpha=0.05, check which are significant
    # Note: The exact result depends on the BH calculation
    # We just verify the boolean column exists and is consistent
    for _, row in result.iterrows():
        if row['adjusted_p'] < 0.05:
            assert row['significant'] == True
        else:
            assert row['significant'] == False
