import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from analysis.sensitivity import (
    load_complexity_scores,
    load_aggregated_d_scores,
    re_categorize_complexity,
    run_analysis_for_threshold,
    run_loio_analysis,
    run_sensitivity_analysis,
    MIN_PARTICIPANTS_PER_CONDITION
)

@pytest.fixture
def sample_complexity_data():
    """Create sample complexity data for testing."""
    data = {
        'filename': ['img1.png', 'img2.png', 'img3.png', 'img4.png', 'img5.png'],
        'edge_density': [0.1, 0.2, 0.3, 0.4, 0.5],
        'entropy': [1.0, 2.0, 3.0, 4.0, 5.0],
        'fractal_dim': [1.2, 1.5, 1.8, 2.1, 2.4],
        'complexity_category': ['Low', 'Low', 'Low', 'High', 'High']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_d_scores_data():
    """Create sample D-scores data for testing."""
    data = {
        'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'session_id': ['S1', 'S1', 'S1', 'S1', 'S1'],
        'complexity_condition': ['Low', 'Low', 'Low', 'High', 'High'],
        'd_score': [0.5, 0.6, 0.55, 0.7, 0.8],
        'n_trials_valid': [50, 50, 50, 50, 50],
        'status': ['valid', 'valid', 'valid', 'valid', 'valid']
    }
    return pd.DataFrame(data)

def test_re_categorize_complexity_shift_positive(sample_complexity_data):
    """Test that positive shift increases threshold and moves images to Low."""
    sd_edge_density = sample_complexity_data['edge_density'].std()
    shift = 0.10
    
    df_recat = re_categorize_complexity(sample_complexity_data, shift, sd_edge_density)
    
    # With positive shift, threshold increases, so more images should be 'Low'
    # Original median is 0.3, new threshold is 0.3 + 0.1*sd
    # Images with edge_density <= new_threshold should be 'Low'
    
    # Check that the number of 'Low' images increased or stayed same
    original_low_count = (sample_complexity_data['complexity_category'] == 'Low').sum()
    new_low_count = (df_recat['complexity_category'] == 'Low').sum()
    
    assert new_low_count >= original_low_count, "Positive shift should not decrease Low count"

def test_re_categorize_complexity_shift_negative(sample_complexity_data):
    """Test that negative shift decreases threshold and moves images to High."""
    sd_edge_density = sample_complexity_data['edge_density'].std()
    shift = -0.10
    
    df_recat = re_categorize_complexity(sample_complexity_data, shift, sd_edge_density)
    
    # With negative shift, threshold decreases, so more images should be 'High'
    original_high_count = (sample_complexity_data['complexity_category'] == 'High').sum()
    new_high_count = (df_recat['complexity_category'] == 'High').sum()
    
    assert new_high_count >= original_high_count, "Negative shift should not decrease High count"

def test_run_analysis_for_threshold_insufficient_participants(sample_complexity_data, sample_d_scores_data):
    """Test that insufficient participants returns invalid status."""
    sd_edge_density = sample_complexity_data['edge_density'].std()
    
    # Create data with insufficient participants
    insufficient_d_scores = sample_d_scores_data.head(3)  # Only 3 participants
    
    result = run_analysis_for_threshold(insufficient_d_scores, sample_complexity_data, 0.0, sd_edge_density)
    
    assert result['status'] == 'invalid'
    assert 'n <' in result['reason']

def test_run_loio_analysis(sample_complexity_data, sample_d_scores_data):
    """Test LOIO analysis returns results for each image."""
    # This is a simplified test; full LOIO requires more complex setup
    results = run_loio_analysis(sample_d_scores_data, sample_complexity_data)
    
    assert len(results) == len(sample_complexity_data)
    for result in results:
        assert 'image' in result
        assert 'status' in result

def test_run_sensitivity_analysis_integration(sample_complexity_data, sample_d_scores_data, tmp_path):
    """Integration test for full sensitivity analysis."""
    # Mock the file paths
    with patch('analysis.sensitivity.get_data_path') as mock_get_path:
        # Create temporary files
        complexity_path = tmp_path / "complexity_scores.csv"
        d_scores_path = tmp_path / "aggregated_d_scores.csv"
        counterbalance_path = tmp_path / "counterbalance_assignment.csv"
        results_path = tmp_path / "sensitivity_results.json"
        
        sample_complexity_data.to_csv(complexity_path, index=False)
        sample_d_scores_data.to_csv(d_scores_path, index=False)
        
        # Create a minimal counterbalance assignment
        counterbalance_data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'session_order': ['Low-High', 'Low-High', 'Low-High', 'High-Low', 'High-Low'],
            'stimulus_set_id': ['SetA', 'SetA', 'SetA', 'SetB', 'SetB']
        }
        pd.DataFrame(counterbalance_data).to_csv(counterbalance_path, index=False)
        
        # Mock the get_data_path function
        def mock_path(name):
            if "complexity_scores.csv" in name:
                return complexity_path
            elif "aggregated_d_scores.csv" in name:
                return d_scores_path
            elif "counterbalance_assignment.csv" in name:
                return counterbalance_path
            else:
                return results_path
        
        mock_get_path.side_effect = mock_path
        
        # Run analysis
        results = run_sensitivity_analysis()
        
        # Check results structure
        assert 'threshold_sweep' in results
        assert 'loio_results' in results
        assert len(results['threshold_sweep']) > 0
        assert len(results['loio_results']) > 0