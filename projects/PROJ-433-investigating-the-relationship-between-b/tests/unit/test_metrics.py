"""
Unit tests for metrics computation, specifically sliding-window correlation logic.
"""
import numpy as np
import pytest
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import get_seeded_rng
from metrics import compute_sliding_window


def test_sliding_window_correlation_shapes():
    """
    Verify output matrix shape matches expected (n_windows, n_parcels, n_parcels)
    for synthetic input.
    """
    # Configuration
    seed = 42
    n_parcels = 100
    n_timepoints = 300
    window_size = 60
    step_size = 10
    
    # Create synthetic BOLD data: (n_timepoints, n_parcels)
    rng = get_seeded_rng(seed)
    synthetic_bold = rng.standard_normal((n_timepoints, n_parcels))
    
    # Compute sliding window correlations
    correlation_matrices = compute_sliding_window(
        bold_data=synthetic_bold,
        window_size=window_size,
        step_size=step_size
    )
    
    # Calculate expected number of windows
    # Number of windows = floor((n_timepoints - window_size) / step_size) + 1
    expected_n_windows = (n_timepoints - window_size) // step_size + 1
    expected_shape = (expected_n_windows, n_parcels, n_parcels)
    
    # Verify output shape
    assert correlation_matrices.shape == expected_shape, (
        f"Expected shape {expected_shape}, got {correlation_matrices.shape}"
    )
    
    # Verify data type is float (correlation coefficients)
    assert np.issubdtype(correlation_matrices.dtype, np.floating), (
        f"Expected float dtype, got {correlation_matrices.dtype}"
    )
    
    # Verify correlation values are in valid range [-1, 1]
    assert np.all(correlation_matrices >= -1.0) and np.all(correlation_matrices <= 1.0), (
        "Correlation values must be in range [-1, 1]"
    )
    
    # Verify diagonal of each window's correlation matrix is 1.0
    for i in range(expected_n_windows):
        np.testing.assert_array_almost_equal(
            np.diag(correlation_matrices[i]),
            np.ones(n_parcels),
            decimal=6,
            err_msg=f"Diagonal of window {i} should be all 1s"
        )