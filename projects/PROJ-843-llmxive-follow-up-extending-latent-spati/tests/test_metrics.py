import os
import sys
import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from eval.metrics import (
    load_npy_safe,
    calculate_world_score,
    calculate_sparse_consistency_score,
    calculate_fid,
    compute_unified_geometric_error,
    main
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directories for testing."""
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    results_dir = data_dir / "results"
    raw_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    return data_dir, raw_dir, results_dir

@pytest.fixture
def sample_dense_frames():
    """Generate sample dense frames for testing."""
    # Create a 10-frame sequence of 64x64 RGB images
    frames = np.random.rand(10, 64, 64, 3).astype(np.float32)
    return frames

@pytest.fixture
def sample_sparse_frames():
    """Generate sample sparse warped frames for testing."""
    # Create a 10-frame sequence of 64x64 RGB images
    frames = np.random.rand(10, 64, 64, 3).astype(np.float32)
    return frames

def test_load_npy_safe_exists(tmp_path):
    """Test loading an existing .npy file."""
    test_file = tmp_path / "test.npy"
    data = np.array([1, 2, 3])
    np.save(test_file, data)
    
    result = load_npy_safe(test_file)
    assert result is not None
    assert np.array_equal(result, data)

def test_load_npy_safe_missing(tmp_path):
    """Test loading a non-existent .npy file."""
    result = load_npy_safe(tmp_path / "nonexistent.npy")
    assert result is None

def test_calculate_world_score_basic(sample_dense_frames, sample_sparse_frames):
    """Test basic WorldScore calculation."""
    result = calculate_world_score(sample_dense_frames, sample_sparse_frames)
    
    assert "world_score" in result
    assert "components" in result
    assert isinstance(result["world_score"], float)
    assert 0.0 <= result["world_score"] <= 1.0  # Score should be normalized

def test_calculate_world_score_missing_data():
    """Test WorldScore with missing data."""
    result = calculate_world_score(None, np.array([1, 2, 3]))
    assert result["world_score"] == 0.0
    assert "error" in result

def test_calculate_sparse_consistency_score_basic(sample_sparse_frames):
    """Test basic Sparse-Consistency Score calculation."""
    result = calculate_sparse_consistency_score(sample_sparse_frames)
    
    assert "sparse_consistency_score" in result
    assert "components" in result
    assert isinstance(result["sparse_consistency_score"], float)
    assert 0.0 <= result["sparse_consistency_score"] <= 1.0

def test_calculate_sparse_consistency_score_missing():
    """Test Sparse-Consistency Score with missing data."""
    result = calculate_sparse_consistency_score(None)
    assert result["sparse_consistency_score"] == 0.0
    assert "error" in result

def test_calculate_fid_basic(sample_dense_frames, sample_sparse_frames):
    """Test basic FID calculation (should use fallback)."""
    result = calculate_fid(sample_dense_frames, sample_sparse_frames)
    
    assert "fid_score" in result
    assert "components" in result
    # FID can be any non-negative value, but should be finite
    assert np.isfinite(result["fid_score"])

def test_calculate_fid_missing_data():
    """Test FID with missing data."""
    result = calculate_fid(None, np.array([1, 2, 3]))
    assert result["fid_score"] == float('inf')
    assert "error" in result

def test_compute_unified_geometric_error_basic(sample_sparse_frames):
    """Test basic Unified Geometric Error calculation."""
    result = compute_unified_geometric_error(sample_sparse_frames)
    
    assert "unified_geometric_error" in result
    assert "components" in result
    assert isinstance(result["unified_geometric_error"], float)
    assert result["unified_geometric_error"] >= 0.0

def test_compute_unified_geometric_error_missing():
    """Test Unified Geometric Error with missing data."""
    result = compute_unified_geometric_error(None)
    assert result["unified_geometric_error"] == float('inf')
    assert "error" in result

def test_main_integration(tmp_path, sample_dense_frames, sample_sparse_frames, monkeypatch):
    """Test the main function integration."""
    # Setup paths
    data_dir, raw_dir, results_dir = tmp_path / "data", tmp_path / "data" / "raw", tmp_path / "data" / "results"
    
    # Save test data
    np.save(raw_dir / "dense_baseline_frames.npy", sample_dense_frames)
    np.save(results_dir / "sparse_warped_frames.npy", sample_sparse_frames)
    
    # Mock config functions to use temp paths
    def mock_get_raw_dir():
        return raw_dir
    
    def mock_get_results_dir():
        return results_dir
    
    monkeypatch.setattr("eval.metrics.get_raw_dir", mock_get_raw_dir)
    monkeypatch.setattr("eval.metrics.get_results_dir", mock_get_results_dir)
    
    # Run main
    result = main()
    
    # Verify output file was created
    output_path = results_dir / "metrics.json"
    assert output_path.exists()
    
    # Verify content
    with open(output_path) as f:
        saved_data = json.load(f)
    
    assert "world_score" in saved_data
    assert "sparse_consistency_score" in saved_data
    assert "fid" in saved_data
    assert "unified_geometric_error" in saved_data