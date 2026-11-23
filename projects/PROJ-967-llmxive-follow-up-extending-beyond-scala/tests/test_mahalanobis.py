import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module functions
from mahalanobis_distance import (
    calculate_mahalanobis_distance,
    load_model_selection,
    load_covariance_matrix,
    load_global_mean,
    load_cleaned_data,
    save_results,
    main
)

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "processed"
        results_dir = Path(tmpdir) / "results"
        data_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        yield data_dir, results_dir

@pytest.fixture
def sample_df():
    data = {
        'sample_id': ['s1', 's2', 's3', 's4'],
        'Alignment': [5.0, 6.0, 4.0, 5.5],
        'Realism': [5.0, 5.5, 4.5, 5.0],
        'Aesthetics': [5.0, 4.0, 6.0, 5.5],
        'Plausibility': [5.0, 5.0, 5.0, 5.0],
        'student_scalar': [4.5, 5.5, 4.0, 5.0],
        'primary_dimension': ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_cov_matrix():
    # A simple positive definite matrix
    return np.array([
        [1.0, 0.1, 0.1, 0.1],
        [0.1, 1.0, 0.1, 0.1],
        [0.1, 0.1, 1.0, 0.1],
        [0.1, 0.1, 0.1, 1.0]
    ])

@pytest.fixture
def sample_mean():
    return np.array([5.0, 5.0, 5.0, 5.0])

def test_calculate_mahalanobis_distance_valid(sample_df, sample_cov_matrix, sample_mean):
    distances = calculate_mahalanobis_distance(sample_df, sample_cov_matrix, sample_mean)
    assert len(distances) == 4
    assert all(isinstance(d, (float, np.floating)) for d in distances)
    # First point is exactly the mean, so distance should be 0
    assert distances[0] == 0.0

def test_calculate_mahalanobis_distance_singular_matrix(sample_df, sample_mean):
    # Create a singular matrix (rank < 4)
    singular_cov = np.array([
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0]
    ])
    # Should not raise, should use pseudo-inverse
    distances = calculate_mahalanobis_distance(sample_df, singular_cov, sample_mean)
    assert len(distances) == 4

def test_main_rf_model(temp_dirs, sample_df, sample_cov_matrix, sample_mean):
    data_dir, results_dir = temp_dirs
    
    # Save model selection
    with open(data_dir / "model_selection.json", 'w') as f:
        json.dump({"model_type": "rf"}, f)
    
    # Save covariance matrix
    with open(results_dir / "covariance_matrix.json", 'w') as f:
        json.dump({"matrix": sample_cov_matrix.tolist()}, f)
    
    # Save global mean
    with open(results_dir / "global_mean.json", 'w') as f:
        json.dump({"mean": sample_mean.tolist()}, f)
    
    # Save cleaned data
    sample_df.to_parquet(data_dir / "cleaned_data.parquet")
    
    # Mock the functions that load from disk to use our temp data
    # (Actually, the main function loads from disk, so we just need the files there)
    
    # Run main
    exit_code = main()
    assert exit_code == 0
    
    # Check output file
    scores_path = data_dir / "entanglement_scores.csv"
    assert scores_path.exists()
    
    output_df = pd.read_csv(scores_path)
    assert 'mahalanobis_distance' in output_df.columns

def test_main_ridge_model(temp_dirs):
    data_dir, results_dir = temp_dirs
    
    # Save model selection as ridge
    with open(data_dir / "model_selection.json", 'w') as f:
        json.dump({"model_type": "ridge"}, f)
    
    # Run main
    exit_code = main()
    assert exit_code == 0
    
    # Check status file
    status_path = data_dir / "feature_status.json"
    assert status_path.exists()
    with open(status_path, 'r') as f:
        status = json.load(f)
    assert status['mahalanobis_distance'] == 'skipped'

def test_main_fail_model(temp_dirs):
    data_dir, results_dir = temp_dirs
    
    # Save model selection as fail
    with open(data_dir / "model_selection.json", 'w') as f:
        json.dump({"model_type": "fail"}, f)
    
    # Run main
    exit_code = main()
    assert exit_code == 0
    
    # Check status file
    status_path = data_dir / "feature_status.json"
    assert status_path.exists()
    with open(status_path, 'r') as f:
        status = json.load(f)
    assert status['mahalanobis_distance'] == 'skipped'
