"""
Unit tests for compute_metrics.py
"""
import pytest
import numpy as np
from scipy.spatial import cKDTree

from code.data.compute_metrics import (
    _apply_periodic_wrap,
    _build_periodic_kdtree,
    calculate_local_overdensity
)
from code.config import BOX_SIZE_MPC, RANDOM_SEED

def test_apply_periodic_wrap():
    """Test periodic wrapping of coordinates."""
    coords = np.array([[-1.0, 0.0, 0.0], [107.0, 0.0, 0.0]])
    wrapped = _apply_periodic_wrap(coords, BOX_SIZE_MPC)
    # -1.0 should wrap to 105.5 (106.5 - 1.0)
    # 107.0 should wrap to 0.5
    expected = np.array([[105.5, 0.0, 0.0], [0.5, 0.0, 0.0]])
    assert np.allclose(wrapped, expected)

def test_build_periodic_kdtree():
    """Test KDTree creation."""
    positions = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    tree = _build_periodic_kdtree(positions, BOX_SIZE_MPC)
    assert isinstance(tree, cKDTree)
    assert len(tree.data) == 2

def test_calculate_local_overdensity():
    """Test overdensity calculation with a simple setup."""
    # Create a uniform distribution of points
    np.random.seed(RANDOM_SEED)
    n_points = 1000
    positions = np.random.uniform(0, BOX_SIZE_MPC, size=(n_points, 3))
    
    radius = 5.0
    overdensities = calculate_local_overdensity(
        positions, 
        BOX_SIZE_MPC, 
        radius, 
        seed=RANDOM_SEED
    )
    
    # For a uniform distribution, overdensity should be close to 0
    mean_delta = np.mean(overdensities)
    std_delta = np.std(overdensities)
    
    # Allow some variance due to Poisson noise
    assert abs(mean_delta) < 0.5, f"Mean overdensity {mean_delta} is too far from 0"
    assert std_delta < 2.0, f"Std dev {std_delta} is too high for uniform distribution"

def test_overdensity_with_clump():
    """Test overdensity calculation with a known clump."""
    np.random.seed(RANDOM_SEED)
    n_points = 1000
    positions = np.random.uniform(0, BOX_SIZE_MPC, size=(n_points, 3))
    
    # Add a clump at the center
    center = np.array([BOX_SIZE_MPC/2, BOX_SIZE_MPC/2, BOX_SIZE_MPC/2])
    clump = np.random.normal(center, 0.1, size=(100, 3))
    positions = np.vstack([positions, clump])
    
    radius = 0.5
    overdensities = calculate_local_overdensity(
        positions, 
        BOX_SIZE_MPC, 
        radius, 
        seed=RANDOM_SEED
    )
    
    # The overdensity in the clump should be significantly positive
    # We check the max overdensity to see if the clump is detected
    max_delta = np.max(overdensities)
    assert max_delta > 2.0, f"Max overdensity {max_delta} is too low for a clump"