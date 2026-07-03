"""
Unit tests for sensitivity clustering (T024b).
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features.sensitivity_clustering import perform_sensitivity_clustering, save_clustering_results

@pytest.fixture
def sample_features():
    """Create a sample features DataFrame."""
    data = {
        'participant_id': [f'P{i:03d}' for i in range(1, 51)],
        'eye_to_mouth_ratio': np.random.uniform(0.5, 2.5, 50),
        'fixation_duration': np.random.uniform(100, 500, 50),
        'saccade_amplitude': np.random.uniform(1, 10, 50)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

def test_perform_sensitivity_clustering_k2_k3(sample_features):
    """Test that clustering produces results for k=2 and k=3."""
    results = perform_sensitivity_clustering(sample_features, k_values=[2, 3])
    
    assert 2 in results
    assert 3 in results
    
    df_k2 = results[2]
    df_k3 = results[3]
    
    # Check that label columns exist
    assert 'cluster_label_k2' in df_k2.columns
    assert 'cluster_label_k3' in df_k3.columns
    
    # Check that labels are integers and within range
    assert df_k2['cluster_label_k2'].min() >= 0
    assert df_k2['cluster_label_k2'].max() <= 1
    
    assert df_k3['cluster_label_k3'].min() >= 0
    assert df_k3['cluster_label_k3'].max() <= 2
    
    # Check that row counts match
    assert len(df_k2) == len(sample_features)
    assert len(df_k3) == len(sample_features)

def test_save_clustering_results(temp_output_dir, sample_features):
    """Test that results are saved to CSV files."""
    results = perform_sensitivity_clustering(sample_features, k_values=[2, 3])
    saved_files = save_clustering_results(results, temp_output_dir)
    
    assert len(saved_files) == 2
    
    expected_files = ['labels_k2.csv', 'labels_k3.csv']
    for expected in expected_files:
        filepath = temp_output_dir / expected
        assert filepath.exists(), f"Expected file {filepath} was not created"
        
        # Verify content
        df = pd.read_csv(filepath)
        assert 'participant_id' in df.columns
        assert 'eye_to_mouth_ratio' in df.columns
        assert f'cluster_label_k{expected[-5]}' in df.columns # k2 or k3

def test_clustering_with_missing_ratio_column(sample_features, temp_output_dir):
    """Test clustering when ratio column is missing but raw data exists."""
    # Remove the ratio column
    df_no_ratio = sample_features.drop(columns=['eye_to_mouth_ratio'])
    # Add raw eye/mouth columns
    df_no_ratio['fixation_eye'] = np.random.uniform(10, 50, 50)
    df_no_ratio['fixation_mouth'] = np.random.uniform(10, 50, 50)
    
    # This should trigger the fallback logic inside the function
    results = perform_sensitivity_clustering(df_no_ratio, k_values=[2])
    
    assert 2 in results
    assert 'eye_to_mouth_ratio' in results[2].columns # Should be calculated
    assert 'cluster_label_k2' in results[2].columns
