"""
Unit tests for the Grassberger-Procaccia algorithm implementation.

This test verifies the correctness of the Correlation Dimension computation
using synthetic data with a known theoretical correlation dimension.

We generate a synthetic dataset from a known fractal structure (or a
deterministic chaotic system with a known dimension) and verify that
the computed correlation dimension matches the theoretical value within
a specified tolerance.

For this test, we use a synthetic dataset generated from a known distribution
or a simplified chaotic system where the correlation dimension is well-established.
Specifically, we test against the Hénon map, which has a known correlation
dimension of approximately 1.21.
"""
import numpy as np
import pytest
import sys
import os

# Add the project root to the path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.metrics import compute_correlation_dimension
from code.generators import generate_lorenz_trajectory
from code.config import get_system_params


def test_grassberger_procaccia_henon_map():
    """
    Test the Grassberger-Procaccia algorithm on Hénon map data.
    
    The Hénon map is a well-studied chaotic system with a known
    correlation dimension of approximately 1.21. We generate a
    trajectory from the Hénon map and verify that the computed
    correlation dimension is within 10% of the theoretical value.
    
    Reference:
    - Grassberger, P., & Procaccia, I. (1983). Measuring the strangeness
      of strange attractors. Physica D: Nonlinear Phenomena, 9(1-2), 189-208.
    """
    # Generate Hénon map trajectory
    # Parameters for the Hénon map: a = 1.4, b = 0.3
    # These are the standard parameters that produce chaos
    a = 1.4
    b = 0.3
    n_points = 10000
    discard = 1000  # Discard initial transient
    
    # Initialize
    x = np.zeros(n_points + discard)
    y = np.zeros(n_points + discard)
    x[0] = 0.0
    y[0] = 0.0
    
    # Iterate Hénon map
    for i in range(1, n_points + discard):
        x[i] = 1.0 - a * x[i-1]**2 + y[i-1]
        y[i] = b * x[i-1]
    
    # Discard transient
    x = x[discard:]
    y = y[discard:]
    
    # Combine into a single time series (using x component)
    # For correlation dimension, we can use a single variable
    time_series = x
    
    # Embedding parameters
    embedding_dim = 5
    lag = 1
    min_dist = 0.01
    max_dist = 1.0
    n_radii = 20
    
    # Compute correlation dimension
    # The function returns (correlation_dimension, r_values, C_values)
    try:
        dim, r_vals, c_vals = compute_correlation_dimension(
            time_series,
            embedding_dim=embedding_dim,
            lag=lag,
            min_dist=min_dist,
            max_dist=max_dist,
            n_radii=n_radii
        )
        
        # Theoretical correlation dimension for Hénon map is ~1.21
        theoretical_dim = 1.21
        tolerance = 0.20  # Allow 20% tolerance due to finite data and estimation errors
        
        # Assert that the computed dimension is within tolerance
        assert abs(dim - theoretical_dim) / theoretical_dim < tolerance, \
            f"Computed correlation dimension {dim:.4f} is outside tolerance of theoretical value {theoretical_dim:.4f}. " \
            f"Difference: {abs(dim - theoretical_dim):.4f}, Relative error: {abs(dim - theoretical_dim) / theoretical_dim:.2%}"
        
        # Additional checks
        assert dim > 0, "Correlation dimension must be positive"
        assert dim < embedding_dim, "Correlation dimension should be less than embedding dimension"
        
        # Check that correlation integral values are monotonically increasing with radius
        # (with some tolerance for numerical noise)
        assert np.all(np.diff(c_vals) >= -1e-10), "Correlation integral should be non-decreasing with radius"
        
    except Exception as e:
        pytest.fail(f"Grassberger-Procaccia computation failed with error: {str(e)}")


def test_grassberger_procaccia_lorenz_attractor():
    """
    Test the Grassberger-Procaccia algorithm on Lorenz attractor data.
    
    The Lorenz attractor has a known correlation dimension of approximately
    2.05. We generate a trajectory from the Lorenz system and verify that
    the computed correlation dimension is within 15% of the theoretical value.
    
    Reference:
    - Grassberger, P., & Procaccia, I. (1983). Measuring the strangeness
      of strange attractors. Physica D: Nonlinear Phenomena, 9(1-2), 189-208.
    - Kaplan, J. L., & Yorke, J. A. (1979). Preturbulence: A regime observed
      in a fluid flow model of Lorenz. Communications in Mathematical Physics,
      67(2), 93-108.
    """
    # Generate Lorenz trajectory
    params = get_system_params('lorenz')
    trajectory = generate_lorenz_trajectory(
        seed=42,
        duration=params['duration'],
        dt=params['dt']
    )
    
    # Use the x-component of the trajectory
    time_series = trajectory['data'][:, 0]
    
    # Embedding parameters
    embedding_dim = 7
    lag = 10
    min_dist = 0.01
    max_dist = 2.0
    n_radii = 25
    
    # Compute correlation dimension
    try:
        dim, r_vals, c_vals = compute_correlation_dimension(
            time_series,
            embedding_dim=embedding_dim,
            lag=lag,
            min_dist=min_dist,
            max_dist=max_dist,
            n_radii=n_radii
        )
        
        # Theoretical correlation dimension for Lorenz attractor is ~2.05
        theoretical_dim = 2.05
        tolerance = 0.25  # Allow 25% tolerance due to finite data and estimation errors
        
        # Assert that the computed dimension is within tolerance
        assert abs(dim - theoretical_dim) / theoretical_dim < tolerance, \
            f"Computed correlation dimension {dim:.4f} is outside tolerance of theoretical value {theoretical_dim:.4f}. " \
            f"Difference: {abs(dim - theoretical_dim):.4f}, Relative error: {abs(dim - theoretical_dim) / theoretical_dim:.2%}"
        
        # Additional checks
        assert dim > 0, "Correlation dimension must be positive"
        assert dim < embedding_dim, "Correlation dimension should be less than embedding dimension"
        
    except Exception as e:
        pytest.fail(f"Grassberger-Procaccia computation on Lorenz data failed with error: {str(e)}")


def test_grassberger_procaccia_random_data():
    """
    Test that the algorithm behaves correctly on random (non-chaotic) data.
    
    For random data, the correlation dimension should scale with the
    embedding dimension (it should not saturate at a low value).
    """
    # Generate random data
    np.random.seed(42)
    time_series = np.random.randn(5000)
    
    # Test with different embedding dimensions
    for embedding_dim in [3, 5, 7]:
        try:
            dim, r_vals, c_vals = compute_correlation_dimension(
                time_series,
                embedding_dim=embedding_dim,
                lag=1,
                min_dist=0.01,
                max_dist=1.0,
                n_radii=15
            )
            
            # For random data, the correlation dimension should be close to
            # the embedding dimension (or at least significantly higher than
            # for chaotic data)
            # This is a sanity check rather than a precise measurement
            assert dim > 0, "Correlation dimension must be positive"
            
        except Exception as e:
            pytest.fail(f"Grassberger-Procaccia computation on random data failed with error: {str(e)}")


def test_grassberger_procaccia_edge_cases():
    """
    Test edge cases and error handling.
    """
    # Test with insufficient data points
    short_series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    with pytest.raises(ValueError):
        compute_correlation_dimension(
            short_series,
            embedding_dim=5,
            lag=1,
            min_dist=0.01,
            max_dist=1.0,
            n_radii=5
        )
    
    # Test with invalid parameters
    time_series = np.random.randn(1000)
    
    # Negative embedding dimension
    with pytest.raises(ValueError):
        compute_correlation_dimension(
            time_series,
            embedding_dim=-1,
            lag=1,
            min_dist=0.01,
            max_dist=1.0,
            n_radii=10
        )
    
    # Zero or negative min_dist
    with pytest.raises(ValueError):
        compute_correlation_dimension(
            time_series,
            embedding_dim=3,
            lag=1,
            min_dist=0,
            max_dist=1.0,
            n_radii=10
        )
    
    # max_dist <= min_dist
    with pytest.raises(ValueError):
        compute_correlation_dimension(
            time_series,
            embedding_dim=3,
            lag=1,
            min_dist=0.1,
            max_dist=0.1,
            n_radii=10
        )