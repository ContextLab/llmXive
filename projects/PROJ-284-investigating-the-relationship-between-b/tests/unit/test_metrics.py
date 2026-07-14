import pytest
import numpy as np
from pathlib import Path
from code.data.metrics import calculate_connectivity_matrix, ConnectivityMatrix

def test_connectivity_matrix_shape():
    """Test that the connectivity matrix is 400x400."""
    # Generate synthetic time series for testing
    n_timepoints = 100
    n_rois = 400
    time_series = np.random.randn(n_timepoints, n_rois)
    
    conn_matrix = calculate_connectivity_matrix(time_series)
    
    assert isinstance(conn_matrix, ConnectivityMatrix)
    assert conn_matrix.data.shape == (n_rois, n_rois)
    assert conn_matrix.atlas_id == "Schaefer400"

def test_connectivity_matrix_symmetry():
    """Test that the connectivity matrix is symmetric."""
    n_timepoints = 100
    n_rois = 400
    time_series = np.random.randn(n_timepoints, n_rois)
    
    conn_matrix = calculate_connectivity_matrix(time_series)
    
    data = conn_matrix.data
    assert np.allclose(data, data.T)

def test_connectivity_matrix_diagonal():
    """Test that the diagonal of the connectivity matrix is 1.0."""
    n_timepoints = 100
    n_rois = 400
    time_series = np.random.randn(n_timepoints, n_rois)
    
    conn_matrix = calculate_connectivity_matrix(time_series)
    
    data = conn_matrix.data
    assert np.allclose(np.diag(data), 1.0)
