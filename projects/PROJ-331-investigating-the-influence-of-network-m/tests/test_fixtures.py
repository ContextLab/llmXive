"""
Basic sanity tests for the conftest fixtures to ensure they generate valid data.
These tests verify that the fixtures created in conftest.py work as expected.
"""
import os
import numpy as np
import pytest
from pathlib import Path

def test_test_root_exists(test_root):
    """Verify the temporary test root directory exists."""
    assert test_root.exists()
    assert test_root.is_dir()

def test_data_directories_created(data_raw_dir, data_processed_dir, data_logs_dir, results_dir):
    """Verify all required data subdirectories are created."""
    assert data_raw_dir.exists()
    assert data_processed_dir.exists()
    assert data_logs_dir.exists()
    assert results_dir.exists()

def test_small_binary_adj_fixture(small_binary_adj):
    """Verify the small binary adjacency matrix is valid."""
    assert small_binary_adj.exists()
    adj = np.load(small_binary_adj)
    assert adj.shape == (10, 10)
    assert adj.dtype in [np.float32, np.float64, np.int32, np.int64]
    # Check for binary values (0 or 1)
    unique_vals = np.unique(adj)
    assert set(unique_vals).issubset({0.0, 1.0})

def test_small_weighted_adj_fixture(small_weighted_adj, small_binary_adj):
    """Verify the weighted adjacency matrix is valid and consistent with binary."""
    assert small_weighted_adj.exists()
    weighted = np.load(small_weighted_adj)
    binary = np.load(small_binary_adj)
    
    assert weighted.shape == binary.shape
    assert weighted.dtype in [np.float32, np.float64, np.int32, np.int64]
    
    # Check that non-zero entries in weighted correspond to 1s in binary
    # and that zero entries correspond
    assert np.allclose((weighted > 0).astype(int), binary)
    # Check weights are positive where non-zero
    assert np.all(weighted[weighted > 0] > 0)

def test_mock_timeseries_fixture(mock_timeseries):
    """Verify the mock timeseries fixture is valid."""
    assert mock_timeseries.exists()
    ts = np.load(mock_timeseries)
    assert ts.shape == (10, 200)
    assert np.issubdtype(ts.dtype, np.floating)

def test_mock_atlas_fixture(mock_atlas_nii):
    """Verify the mock atlas file exists."""
    assert mock_atlas_nii.exists()

def test_mock_streamlines_fixture(mock_streamlines_trk):
    """Verify the mock streamlines file exists."""
    assert mock_streamlines_trk.exists()

def test_manifest_fixture(mock_subject_data_json):
    """Verify the subject manifest JSON is valid."""
    import json
    assert mock_subject_data_json.exists()
    with open(mock_subject_data_json, 'r') as f:
        data = json.load(f)
    assert "sub-001" in data
    assert "dwi_path" in data["sub-001"]
    assert "rsfmri_path" in data["sub-001"]

def test_env_vars_set(setup_env_vars, test_root):
    """Verify environment variables are set correctly during tests."""
    assert os.environ.get("PROJECT_ROOT") == str(test_root)
    assert os.environ.get("DATA_RAW_DIR") == str(test_root / "data" / "raw")
    assert os.environ.get("DATA_PROCESSED_DIR") == str(test_root / "data" / "processed")