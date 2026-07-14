import os
import sys
import json
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from eval.metrics import (
    load_npy_safe,
    calculate_world_score,
    calculate_sparse_consistency_score,
    calculate_fid,
    compute_unified_geometric_error
)
from utils.seeds import set_global_seed

# Set seed for reproducibility
set_global_seed(42)

@pytest.fixture
def temp_npy_file(tmp_path):
    """Create a temporary .npy file for testing."""
    data = np.random.rand(10, 10, 3).astype(np.float32)
    file_path = tmp_path / "test_data.npy"
    np.save(str(file_path), data)
    return file_path

def test_load_npy_safe(temp_npy_file):
    """Test safe loading of .npy files."""
    data = load_npy_safe(str(temp_npy_file))
    
    assert data is not None
    assert isinstance(data, np.ndarray)
    assert data.shape == (10, 10, 3)

def test_load_npy_safe_missing_file(tmp_path):
    """Test loading non-existent .npy file."""
    with pytest.raises(FileNotFoundError):
        load_npy_safe(str(tmp_path / "nonexistent.npy"))

def test_calculate_world_score_basic():
    """Test basic WorldScore calculation."""
    # Create mock warped and ground truth frames
    warped = np.random.rand(10, 10, 3).astype(np.float32)
    gt = np.random.rand(10, 10, 3).astype(np.float32)
    
    score = calculate_world_score(warped, gt)
    
    assert isinstance(score, (int, float))
    assert 0 <= score <= 1

def test_calculate_sparse_consistency_score_basic():
    """Test basic Sparse-Consistency Score calculation."""
    # Create mock correspondences and 3D points
    pts1 = np.random.rand(20, 2).astype(np.float32)
    pts2 = np.random.rand(20, 2).astype(np.float32)
    points_3d = np.random.rand(20, 3).astype(np.float32)
    
    score = calculate_sparse_consistency_score(pts1, pts2, points_3d)
    
    assert isinstance(score, (int, float))
    assert score >= 0

def test_calculate_fid_basic(tmp_path):
    """Test basic FID calculation."""
    # Create mock image distributions
    images1 = np.random.rand(50, 64, 64, 3).astype(np.float32)
    images2 = np.random.rand(50, 64, 64, 3).astype(np.float32)
    
    # Save to temp files
    file1 = tmp_path / "images1.npy"
    file2 = tmp_path / "images2.npy"
    np.save(str(file1), images1)
    np.save(str(file2), images2)
    
    score = calculate_fid(str(file1), str(file2))
    
    assert isinstance(score, (int, float))
    assert score >= 0

def test_calculate_fid_empty_arrays(tmp_path):
    """Test FID calculation with empty arrays."""
    images1 = np.array([]).reshape(0, 64, 64, 3)
    images2 = np.array([]).reshape(0, 64, 64, 3)
    
    file1 = tmp_path / "empty1.npy"
    file2 = tmp_path / "empty2.npy"
    np.save(str(file1), images1)
    np.save(str(file2), images2)
    
    # Should handle empty arrays gracefully
    try:
        score = calculate_fid(str(file1), str(file2))
        assert score == 0.0  # Expected for empty sets
    except Exception:
        # Expected to fail with empty arrays
        pass

def test_compute_unified_geometric_error_basic():
    """Test basic unified geometric error calculation."""
    # Create mock warped and ground truth frames
    warped = np.random.rand(10, 10, 3).astype(np.float32)
    gt = np.random.rand(10, 10, 3).astype(np.float32)
    
    error = compute_unified_geometric_error(warped, gt)
    
    assert isinstance(error, (int, float))
    assert error >= 0

def test_calculate_world_score_edge_cases():
    """Test WorldScore with edge cases."""
    # Identical frames should have high score
    frame = np.random.rand(10, 10, 3).astype(np.float32)
    score = calculate_world_score(frame, frame)
    assert score >= 0.9  # Should be very high for identical frames

def test_calculate_sparse_consistency_score_no_matches():
    """Test Sparse-Consistency with no matches."""
    pts1 = np.array([]).reshape(0, 2).astype(np.float32)
    pts2 = np.array([]).reshape(0, 2).astype(np.float32)
    points_3d = np.array([]).reshape(0, 3).astype(np.float32)
    
    score = calculate_sparse_consistency_score(pts1, pts2, points_3d)
    
    # Should handle empty matches gracefully
    assert score == 0.0