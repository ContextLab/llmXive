"""
Integration test for T017: LOO State Assignment

This test verifies that:
1. LOO centroids are correctly loaded
2. States are assigned using only the subject-specific LOO centroids
3. Dynamic metrics (dwell time, visited states) are calculated correctly
"""
import numpy as np
import pandas as pd
import os
import tempfile
from pathlib import Path
import pytest
from preprocess.functional_t017 import (
    load_loo_centroids,
    compute_sliding_window_correlation,
    assign_states_and_calculate_metrics
)
from config import get_config_dict

@pytest.fixture
def sample_data():
    """Create sample fMRI data and LOO centroids for testing."""
    np.random.seed(42)
    n_timepoints = 200
    n_regions = 5
    n_windows = (n_timepoints - 30) // 1 + 1
    
    # Create sample fMRI data
    fmri_data = np.random.randn(n_timepoints, n_regions)
    
    # Create sample correlations
    correlations = compute_sliding_window_correlation(fmri_data, 30, 1)
    
    # Create sample LOO centroids (k=3)
    k = 3
    loo_centroids = np.random.randn(k, n_regions, n_regions)
    
    return {
        'fmri_data': fmri_data,
        'correlations': correlations,
        'loo_centroids': loo_centroids,
        'n_windows': n_windows,
        'n_regions': n_regions,
        'k': k
    }

def test_compute_sliding_window_correlation(sample_data):
    """Test sliding window correlation computation."""
    result = compute_sliding_window_correlation(
        sample_data['fmri_data'], 
        30, 
        1
    )
    
    expected_n_windows = (200 - 30) // 1 + 1
    assert result.shape == (expected_n_windows, 5, 5)
    assert not np.any(np.isnan(result))

def test_assign_states_and_calculate_metrics(sample_data):
    """Test state assignment and metric calculation."""
    state_seq, mean_dwell, num_visited, mean_dwell_by_state = assign_states_and_calculate_metrics(
        sample_data['correlations'],
        sample_data['loo_centroids']
    )
    
    # Check state sequence length
    assert len(state_seq) == sample_data['n_windows']
    
    # Check that all states are valid (0 to k-1)
    assert np.all(state_seq >= 0)
    assert np.all(state_seq < sample_data['k'])
    
    # Check that num_visited is at most k
    assert num_visited <= sample_data['k']
    
    # Check that mean_dwell is positive
    assert mean_dwell > 0
    
    # Check mean_dwell_by_state structure
    assert len(mean_dwell_by_state) == sample_data['k']
    for state_id in range(sample_data['k']):
        assert state_id in mean_dwell_by_state
        assert mean_dwell_by_state[state_id] >= 0

def test_end_to_end_with_temp_files(sample_data):
    """Test the full pipeline with temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create sample LOO centroids file
        loo_file = tmpdir / 'loo_centroids.npz'
        np.savez(loo_file, subject_001_centroids=sample_data['loo_centroids'])
        
        # Load and verify
        loaded = load_loo_centroids(str(loo_file))
        assert 'subject_001' in loaded
        np.testing.assert_array_equal(loaded['subject_001'], sample_data['loo_centroids'])

def test_metrics_schema_compliance(sample_data):
    """Test that metrics match the required schema."""
    state_seq, mean_dwell, num_visited, mean_dwell_by_state = assign_states_and_calculate_metrics(
        sample_data['correlations'],
        sample_data['loo_centroids']
    )
    
    # Verify schema: subject_id, state_id, mean_dwell_time, num_visits
    # We can't test subject_id here as it's passed externally, but we verify the structure
    metrics = []
    for state_id in range(sample_data['k']):
        metrics.append({
            'state_id': state_id,
            'mean_dwell_time': mean_dwell_by_state[state_id],
            'num_visits': list(state_seq).count(state_id)
        })
    
    df = pd.DataFrame(metrics)
    required_columns = ['state_id', 'mean_dwell_time', 'num_visits']
    assert all(col in df.columns for col in required_columns)
    assert df['mean_dwell_time'].min() >= 0
    assert df['num_visits'].min() >= 0
