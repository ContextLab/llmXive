"""
Unit tests for the feature engineering module (code/features.py).
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure imports from code/ work
from features import (
    setup_logging,
    setup_directories,
    load_raw_dataset,
    load_cleaned_dataset,
    extract_teacher_scores_matrix,
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_global_covariance_and_eigenvalue,
    compute_per_sample_stats,
    calculate_mahalanobis_distance,
    integrate_features,
    save_global_stats,
    save_features_to_csv,
    parse_args,
    main
)

def test_extract_teacher_scores_matrix():
    """Test extraction of teacher scores into a matrix."""
    data = {
        "teacher_scores": [
            {"Alignment": 4.5, "Realism": 3.0, "Aesthetics": 4.0, "Plausibility": 3.5},
            {"Alignment": 4.0, "Realism": 3.5, "Aesthetics": 3.8, "Plausibility": 4.0}
        ]
    }
    df = pd.DataFrame(data)
    matrix = extract_teacher_scores_matrix(df)

    assert matrix.shape == (2, 4)
    assert np.allclose(matrix[0], [4.5, 3.0, 4.0, 3.5])

def test_calculate_variance_and_range():
    """Test variance and range calculation."""
    scores = [4.5, 3.0, 4.0, 3.5]
    variance, range_val = calculate_variance_and_range(scores)

    assert isinstance(variance, float)
    assert isinstance(range_val, float)
    assert variance > 0
    assert range_val > 0

def test_calculate_entropy():
    """Test entropy calculation."""
    # Uniform distribution
    probs = [0.25, 0.25, 0.25, 0.25]
    entropy = calculate_entropy(probs)
    assert np.isclose(entropy, np.log2(4))

    # Deterministic distribution (one value is 1.0)
    probs_det = [1.0, 0.0, 0.0, 0.0]
    entropy_det = calculate_entropy(probs_det)
    assert entropy_det == 0.0

def test_calculate_skewness_and_kurtosis():
    """Test skewness and kurtosis calculation."""
    scores = [1, 2, 2, 3, 4]
    skew, kurt = calculate_skewness_and_kurtosis(scores)

    assert isinstance(skew, float)
    assert isinstance(kurt, float)

def test_calculate_global_covariance_and_eigenvalue():
    """Test global covariance and dominant eigenvalue calculation."""
    matrix = np.array([
        [4.5, 3.0, 4.0, 3.5],
        [4.0, 3.5, 3.8, 4.0],
        [4.2, 3.2, 3.9, 3.6]
    ])
    cov_matrix, eigenvalue = calculate_global_covariance_and_eigenvalue(matrix)

    assert cov_matrix.shape == (4, 4)
    assert eigenvalue > 0
    assert np.all(np.isfinite(eigenvalue))

def test_calculate_mahalanobis_distance():
    """Test Mahalanobis distance calculation."""
    x = np.array([4.5, 3.0, 4.0, 3.5])
    mean = np.array([4.0, 3.2, 3.8, 3.6])
    cov = np.eye(4)  # Identity matrix for simplicity

    dist = calculate_mahalanobis_distance(x, mean, cov)

    assert isinstance(dist, float)
    assert dist >= 0

def test_calculate_mahalanobis_singular_covariance():
    """Test Mahalanobis distance with singular covariance (uses pseudo-inverse)."""
    x = np.array([4.5, 3.0, 4.0, 3.5])
    mean = np.array([4.0, 3.2, 3.8, 3.6])
    # Create a singular covariance matrix
    cov = np.array([
        [1, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

    # Should not raise an error due to pinv
    dist = calculate_mahalanobis_distance(x, mean, cov)
    assert isinstance(dist, float)
    assert np.isfinite(dist)

def test_compute_per_sample_stats():
    """Test per-sample statistical feature computation."""
    data = {
        "teacher_scores": [
            {"Alignment": 4.5, "Realism": 3.0, "Aesthetics": 4.0, "Plausibility": 3.5}
        ]
    }
    df = pd.DataFrame(data)

    result_df = compute_per_sample_stats(df)

    assert "variance" in result_df.columns
    assert "entropy" in result_df.columns
    assert "skewness" in result_df.columns
    assert "kurtosis" in result_df.columns
