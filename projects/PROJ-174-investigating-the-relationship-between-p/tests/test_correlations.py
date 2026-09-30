import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.correlations import (
    load_processed_data,
    extract_pupil_metrics,
    calculate_pearson_correlation,
    benjamini_hochberg_fdr,
    compute_correlations,
    save_results
)

def test_extract_pupil_metrics():
    """Test that pupil metrics are correctly extracted."""
    df = pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S2', 'S2'],
        'pupil_diameter': [2.0, 4.0, 3.0, 5.0]
    })
    
    metrics = extract_pupil_metrics(df)
    
    assert 'peak' in metrics
    assert 'mean' in metrics
    assert 'quantized' in metrics
    
    # Check values
    assert metrics['peak']['S1'] == 4.0
    assert metrics['peak']['S2'] == 5.0
    assert metrics['mean']['S1'] == 3.0
    assert metrics['mean']['S2'] == 4.0

def test_calculate_pearson_correlation():
    """Test Pearson correlation calculation."""
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])
    
    r, p = calculate_pearson_correlation(x, y)
    
    assert np.isclose(r, 1.0)
    assert p < 0.05

def test_benjamini_hochberg_fdr():
    """Test FDR correction logic."""
    p_values = np.array([0.01, 0.04, 0.03, 0.001, 0.05])
    adjusted = benjamini_hochberg_fdr(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(adjusted >= 0) and all(adjusted <= 1)
    # Basic sanity check: adjusted values should generally be larger than raw
    # (though monotonicity correction might make some smaller)
    assert np.any(adjusted > p_values) or np.allclose(adjusted, p_values)

def test_compute_correlations():
    """Test full correlation computation pipeline."""
    # Create mock metrics and features
    metrics_df = pd.DataFrame({
        'peak': [2.0, 3.0],
        'mean': [2.1, 3.1]
    }, index=['S1', 'S2'])
    
    features_df = pd.DataFrame({
        'search_time': [10.0, 20.0],
        'fixation_count': [5, 10]
    }, index=['S1', 'S2'])
    
    results = compute_correlations(metrics_df, features_df)
    
    assert 'metric' in results.columns
    assert 'proxy' in results.columns
    assert 'pearson_r' in results.columns
    assert 'raw_p' in results.columns
    assert 'method' in results.columns
    
    # Check that we have 2 metrics * 2 proxies = 4 rows
    assert len(results) == 4

def test_save_results(tmp_path):
    """Test saving results to CSV."""
    df = pd.DataFrame({
        'metric': ['peak'],
        'proxy': ['search_time'],
        'pearson_r': [0.5],
        'raw_p': [0.05],
        'method': ['pearson']
    })
    
    output_file = tmp_path / "test_results.csv"
    save_results(df, str(output_file))
    
    assert output_file.exists()
    loaded = pd.read_csv(output_file)
    assert len(loaded) == 1
    assert loaded['pearson_r'][0] == 0.5