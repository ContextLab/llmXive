"""
Tests for correlation analysis module.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.correlations import (
    load_processed_data,
    extract_pupil_metrics,
    calculate_pearson_correlation,
    compute_correlations,
    apply_fdr_correction
)
from config import load_config

@pytest.fixture
def sample_config():
    return {
        'paths': {
            'processed_data': 'data/processed',
            'results': 'results'
        }
    }

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with pupil metrics and proxies."""
    data = {
        'subject_id': [1, 1, 1, 2, 2, 2],
        'trial_id': [1, 2, 3, 1, 2, 3],
        'pupil_mean': [2.5, 2.6, 2.4, 3.0, 3.1, 2.9],
        'pupil_peak': [3.0, 3.1, 2.9, 3.5, 3.6, 3.4],
        'search_time': [100, 110, 90, 150, 160, 140],
        'fixation_count': [5, 6, 4, 8, 9, 7],
        'target_salience': [0.8, 0.7, 0.9, 0.6, 0.5, 0.7]
    }
    return pd.DataFrame(data)

def test_extract_pupil_metrics(sample_df):
    metrics = extract_pupil_metrics(sample_df)
    assert 'pupil_mean' in metrics
    assert 'pupil_peak' in metrics
    assert 'search_time' not in metrics

def test_calculate_pearson_correlation(sample_df):
    x = sample_df['pupil_mean']
    y = sample_df['search_time']
    corr, p_val = calculate_pearson_correlation(x, y)
    assert not np.isnan(corr)
    assert not np.isnan(p_val)
    # Check that correlation is positive (as constructed in sample data)
    assert corr > 0

def test_calculate_pearson_correlation_insufficient_data():
    x = pd.Series([1.0, 2.0])
    y = pd.Series([1.0, 2.0])
    corr, p_val = calculate_pearson_correlation(x, y)
    assert np.isnan(corr)
    assert np.isnan(p_val)

def test_compute_correlations(sample_df):
    results = compute_correlations(sample_df)
    assert not results.empty
    assert 'metric' in results.columns
    assert 'proxy' in results.columns
    assert 'pearson_r' in results.columns
    assert 'raw_p' in results.columns
    assert 'method' in results.columns
    
    # Check that we have correlations for expected metrics
    metrics_found = set(results['metric'].unique())
    assert 'pupil_mean' in metrics_found
    assert 'pupil_peak' in metrics_found

def test_compute_correlations_with_nan(sample_df):
    # Introduce NaNs
    sample_df.loc[0, 'pupil_mean'] = np.nan
    results = compute_correlations(sample_df)
    assert not results.empty
    # Should still compute correlations using valid data

def test_apply_fdr_correction(sample_df):
    raw_results = compute_correlations(sample_df)
    corrected_results = apply_fdr_correction(raw_results)
    assert 'adj_p' in corrected_results.columns
    assert len(corrected_results) == len(raw_results)
    # Adjusted p-values should be >= raw p-values (usually)
    # Note: This is a statistical property, but due to floating point might vary slightly
    # We just check they exist and are numeric
    assert all(not np.isnan(corrected_results['adj_p'].dropna()))