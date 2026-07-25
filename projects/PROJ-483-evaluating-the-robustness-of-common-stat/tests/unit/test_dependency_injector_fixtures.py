"""
Unit test fixtures for dependency injection logic validation (Task T009).

This module provides mock data generators and fixtures used to validate
the AR(1), Block Bootstrap, and Spatial Kernel smoothing injection logic.

Note: These are synthetic *inputs* for testing the *injection algorithms*
(e.g., verifying that ar1_inject correctly induces autocorrelation).
They are NOT used as the final research data (which must come from real sources),
but as controlled environments to verify the mathematical correctness of the
dependency injection functions defined in code/dependency_injector.py.
"""
import numpy as np
import pytest
from typing import Tuple, Dict, Any, Optional
import json
from pathlib import Path

# Fixtures for deterministic testing
TEST_SEED = 42
SMALL_N = 50
LARGE_N = 1000

def generate_independent_normal_data(
    n: int, 
    seed: int = TEST_SEED, 
    mean: float = 0.0, 
    std: float = 1.0
) -> np.ndarray:
    """
    Generates a 1D array of independent normal data.
    Used as the baseline 'null' input for dependency injection tests.
    
    Args:
        n: Number of samples.
        seed: Random seed for reproducibility.
        mean: Mean of the distribution.
        std: Standard deviation of the distribution.
        
    Returns:
        np.ndarray: Array of shape (n,) containing independent normal data.
    """
    rng = np.random.default_rng(seed)
    return rng.normal(loc=mean, scale=std, size=n)

def generate_independent_normal_matrix(
    n_rows: int, 
    n_cols: int, 
    seed: int = TEST_SEED
) -> np.ndarray:
    """
    Generates a 2D matrix of independent normal data.
    Useful for testing multivariate injection or spatial proxies.
    
    Args:
        n_rows: Number of samples (observations).
        n_cols: Number of features.
        seed: Random seed.
        
    Returns:
        np.ndarray: Array of shape (n_rows, n_cols).
    """
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0, scale=1, size=(n_rows, n_cols))

def generate_categorical_data(
    n: int, 
    categories: int = 3, 
    seed: int = TEST_SEED
) -> np.ndarray:
    """
    Generates a 1D array of categorical data (integers).
    Used for Chi-squared test validation fixtures.
    
    Args:
        n: Number of samples.
        categories: Number of unique categories (0 to categories-1).
        seed: Random seed.
        
    Returns:
        np.ndarray: Array of shape (n,) containing integers in [0, categories).
    """
    rng = np.random.default_rng(seed)
    return rng.integers(low=0, high=categories, size=n)

def generate_spatial_coordinates(
    n: int, 
    seed: int = TEST_SEED,
    bounds: Tuple[float, float] = (0.0, 100.0)
) -> np.ndarray:
    """
    Generates 2D spatial coordinates for testing spatial kernel smoothing.
    
    Args:
        n: Number of points.
        seed: Random seed.
        bounds: (min, max) tuple for coordinate range.
        
    Returns:
        np.ndarray: Array of shape (n, 2) with x, y coordinates.
    """
    rng = np.random.default_rng(seed)
    return rng.uniform(low=bounds[0], high=bounds[1], size=(n, 2))

def generate_feature_data_for_proxy(
    n: int, 
    n_features: int = 5, 
    n_clusters: int = 3, 
    seed: int = TEST_SEED
) -> np.ndarray:
    """
    Generates feature data specifically designed to have cluster structure
    for testing the feature-space clustering proxy (T037/T041).
    
    Args:
        n: Number of samples.
        n_features: Number of features.
        n_clusters: Number of intended clusters.
        seed: Random seed.
        
    Returns:
        np.ndarray: Array of shape (n, n_features) with clusterable structure.
    """
    rng = np.random.default_rng(seed)
    # Create cluster centers
    centers = rng.uniform(-5, 5, size=(n_clusters, n_features))
    # Assign points to clusters
    labels = rng.integers(0, n_clusters, size=n)
    # Generate points around centers with some noise
    data = np.zeros((n, n_features))
    for i in range(n):
        data[i] = centers[labels[i]] + rng.normal(0, 0.5, size=n_features)
    return data

@pytest.fixture
def independent_data_small():
    """Fixture for small independent dataset (N=50)."""
    return generate_independent_normal_data(SMALL_N, seed=TEST_SEED)

@pytest.fixture
def independent_data_large():
    """Fixture for large independent dataset (N=1000)."""
    return generate_independent_normal_data(LARGE_N, seed=TEST_SEED)

@pytest.fixture
def independent_matrix():
    """Fixture for 2D independent data matrix."""
    return generate_independent_normal_matrix(100, 5, seed=TEST_SEED)

@pytest.fixture
def categorical_data():
    """Fixture for categorical data for Chi-squared tests."""
    return generate_categorical_data(200, categories=4, seed=TEST_SEED)

@pytest.fixture
def spatial_coords():
    """Fixture for 2D spatial coordinates."""
    return generate_spatial_coordinates(150, seed=TEST_SEED)

@pytest.fixture
def clusterable_features():
    """Fixture for feature data with inherent cluster structure."""
    return generate_feature_data_for_proxy(300, n_features=4, n_clusters=3, seed=TEST_SEED)

@pytest.fixture
def temp_manifest_dir(tmp_path):
    """Fixture to create a temporary directory for manifest files."""
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    return manifests_dir

@pytest.fixture
def sample_config():
    """Fixture providing a sample configuration dictionary for tests."""
    return {
        "simulation": {
            "n_replications": 100,
            "alpha": 0.05,
            "seed": TEST_SEED
        },
        "dependency": {
            "ar1_strength": 0.3,
            "block_size": 10,
            "spatial_bandwidth": 5.0
        }
    }
