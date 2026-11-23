"""
Unit Tests for T024b: Sensitivity Clustering (sensitivity_clustering.py)

Tests verify that:
1. K-Means clustering runs for k=2 and k=3.
2. Output DataFrames contain the 'cluster_label' column.
3. Cluster labels are integers within the expected range [0, k-1].
4. The number of rows matches the input (no data loss).
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from features.sensitivity_clustering import (
    perform_sensitivity_clustering,
    load_processed_features,
    save_clustering_results
)

@pytest.fixture
def sample_features_df():
    """Create a mock features DataFrame for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'participant_id': np.random.randint(1, 20, n_samples),
        'trial_id': np.arange(n_samples),
        'fixation_duration_eye': np.random.normal(500, 100, n_samples),
        'fixation_duration_mouth': np.random.normal(300, 80, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    return tmp_path

def test_perform_sensitivity_clustering_k2(sample_features_df):
    """Test clustering with k=2."""
    results = perform_sensitivity_clustering(sample_features_df, [2], logger=MagicMock())
    
    assert 2 in results, "Result for k=2 should exist"
    df_k2 = results[2]
    
    assert 'cluster_label' in df_k2.columns, "cluster_label column must be present"
    assert len(df_k2) == len(sample_features_df), "Row count should match input"
    
    unique_labels = df_k2['cluster_label'].unique()
    assert len(unique_labels) <= 2, "Should have at most 2 unique labels"
    assert all(0 <= l < 2 for l in unique_labels), "Labels should be 0 or 1"

def test_perform_sensitivity_clustering_k3(sample_features_df):
    """Test clustering with k=3."""
    results = perform_sensitivity_clustering(sample_features_df, [3], logger=MagicMock())
    
    assert 3 in results, "Result for k=3 should exist"
    df_k3 = results[3]
    
    assert 'cluster_label' in df_k3.columns, "cluster_label column must be present"
    assert len(df_k3) == len(sample_features_df), "Row count should match input"
    
    unique_labels = df_k3['cluster_label'].unique()
    assert len(unique_labels) <= 3, "Should have at most 3 unique labels"
    assert all(0 <= l < 3 for l in unique_labels), "Labels should be 0, 1, or 2"

def test_perform_sensitivity_clustering_both(sample_features_df):
    """Test clustering with both k=2 and k=3 simultaneously."""
    results = perform_sensitivity_clustering(sample_features_df, [2, 3], logger=MagicMock())
    
    assert 2 in results and 3 in results, "Results for both k=2 and k=3 should exist"
    assert len(results[2]) == len(results[3]), "Both outputs should have same row count"

def test_save_clustering_results(sample_features_df, temp_output_dir):
    """Test saving clustering results to CSV."""
    # Generate results
    results = perform_sensitivity_clustering(sample_features_df, [2, 3], logger=MagicMock())
    
    # Save
    saved_files = save_clustering_results(results, temp_output_dir, logger=MagicMock())
    
    # Verify files exist
    assert len(saved_files) == 2, "Should save 2 files"
    
    file_k2 = temp_output_dir / "labels_k2.csv"
    file_k3 = temp_output_dir / "labels_k3.csv"
    
    assert file_k2.exists(), "labels_k2.csv should be created"
    assert file_k3.exists(), "labels_k3.csv should be created"
    
    # Verify content
    df_k2 = pd.read_csv(file_k2)
    df_k3 = pd.read_csv(file_k3)
    
    assert 'cluster_label' in df_k2.columns
    assert 'cluster_label' in df_k3.columns
    assert len(df_k2) == len(sample_features_df)
    assert len(df_k3) == len(sample_features_df)

def test_missing_columns_raises_error(sample_features_df):
    """Test that missing required columns raises an error."""
    bad_df = sample_features_df.drop(columns=['fixation_duration_eye'])
    
    with pytest.raises(ValueError) as exc_info:
        perform_sensitivity_clustering(bad_df, [2], logger=MagicMock())
    
    assert "Missing columns" in str(exc_info.value) or "Missing required" in str(exc_info.value)

def test_nan_handling(sample_features_df):
    """Test that rows with NaN in features are handled (dropped)."""
    df_with_nan = sample_features_df.copy()
    df_with_nan.loc[0, 'fixation_duration_eye'] = np.nan
    
    # This should not raise, but should log a warning and drop the row
    results = perform_sensitivity_clustering(df_with_nan, [2], logger=MagicMock())
    
    # Result should have one less row
    assert len(results[2]) == len(sample_features_df) - 1