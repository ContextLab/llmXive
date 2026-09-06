"""
Unit tests for Pareto optimization module.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

from code.pareto_optimization import (
    load_encoded_data,
    load_models,
    generate_synthetic_points,
    evaluate,
    run_nsgaII,
    save_results
)
from code.utils.convex_hull import ConvexHullWrapper

@pytest.fixture
def sample_training_data():
    """Create sample training data for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'composition': [f'Al_{i}' for i in range(n_samples)],
        'bulk_modulus': np.random.uniform(50, 200, n_samples),
        'shear_modulus': np.random.uniform(30, 150, n_samples),
        'feature_1': np.random.uniform(0, 1, n_samples),
        'feature_2': np.random.uniform(0, 1, n_samples),
        'feature_3': np.random.uniform(0, 1, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_models():
    """Create dummy models for testing."""
    from sklearn.dummy import DummyRegressor
    return {
        'bulk': DummyRegressor(strategy='mean'),
        'shear': DummyRegressor(strategy='mean')
    }

@pytest.fixture
def sample_validation_report():
    """Create sample validation report."""
    return {
        'uncertainty_variance': 0.1,
        'system_coverage': 0.85
    }

def test_convex_hull_creation(sample_training_data):
    """Test convex hull wrapper creation."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    X = sample_training_data[feature_cols].values
    hull_wrapper = ConvexHullWrapper(X)
    
    assert hull_wrapper is not None
    assert hull_wrapper.get_radius() > 0

def test_point_in_hull(sample_training_data):
    """Test point inclusion in convex hull."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    X = sample_training_data[feature_cols].values
    hull_wrapper = ConvexHullWrapper(X)
    
    # Test centroid (should be inside)
    centroid = np.mean(X, axis=0)
    is_inside, distance = hull_wrapper.is_inside(centroid, return_distance=True)
    assert is_inside
    assert distance >= 0

def test_generate_synthetic_points(sample_training_data):
    """Test synthetic point generation within convex hull."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    X = sample_training_data[feature_cols].values
    hull_wrapper = ConvexHullWrapper(X)
    
    points, valid_flags, distances = generate_synthetic_points(
        sample_training_data, n_points=10, hull_wrapper=hull_wrapper
    )
    
    assert len(points) <= 10
    assert len(valid_flags) == len(points)
    assert len(distances) == len(points)

def test_evaluate_valid_point(sample_training_data, sample_models, sample_validation_report):
    """Test evaluation of a valid point."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    X = sample_training_data[feature_cols].values
    hull_wrapper = ConvexHullWrapper(X)
    
    # Create a point inside the hull (centroid)
    point = np.mean(X, axis=0)
    
    bulk, shear, uncertainty, is_valid, distance = evaluate(
        point, sample_models, hull_wrapper, sample_training_data,
        sample_validation_report, feature_cols
    )
    
    assert is_valid
    assert bulk >= 0
    assert shear >= 0
    assert distance >= 0

def test_evaluate_invalid_point(sample_training_data, sample_models, sample_validation_report):
    """Test evaluation of a point outside the hull."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    X = sample_training_data[feature_cols].values
    hull_wrapper = ConvexHullWrapper(X)
    
    # Create a point far outside the hull
    point = np.mean(X, axis=0) + 10 * np.std(X, axis=0)
    
    bulk, shear, uncertainty, is_valid, distance = evaluate(
        point, sample_models, hull_wrapper, sample_training_data,
        sample_validation_report, feature_cols
    )
    
    assert not is_valid
    assert bulk < 0  # Heavily penalized
    assert shear < 0  # Heavily penalized

def test_save_results(sample_training_data, sample_models, sample_validation_report):
    """Test saving Pareto frontier results."""
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    X = sample_training_data[feature_cols].values
    hull_wrapper = ConvexHullWrapper(X)
    
    # Create dummy Pareto front
    pareto_front = [
        (100.0, 80.0, 0.1, True, 0.5),
        (120.0, 60.0, 0.2, True, 0.3),
        (90.0, 90.0, 0.15, True, 0.4)
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "pareto_frontier.csv"
        
        save_results(pareto_front, str(output_path), sample_training_data, hull_wrapper)
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert 'bulk_modulus' in df.columns
        assert 'shear_modulus' in df.columns
        assert 'is_near_boundary' in df.columns
        assert 'boundary_proximity_flag' in df.columns