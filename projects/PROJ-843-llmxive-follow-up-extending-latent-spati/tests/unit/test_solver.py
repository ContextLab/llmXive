import os
import sys
import json
import tempfile
import shutil
import numpy as np
import cv2
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from geometry.solver import (
    load_correspondences,
    compute_fundamental_matrix,
    triangulate_points,
    validate_reprojection_error,
    process_sequence
)
from utils.seeds import set_global_seed

@pytest.fixture
def temp_correspondences_dir():
    """Create a temporary directory with mock correspondence data."""
    temp_dir = tempfile.mkdtemp()
    
    # Create a mock sequence directory
    seq_dir = Path(temp_dir) / "Static-High" / "seq_001"
    seq_dir.mkdir(parents=True)
    
    # Generate mock correspondences
    np.random.seed(42)
    n_points = 100
    coords_frame1 = np.random.rand(n_points, 2) * 200
    coords_frame2 = coords_frame1 + np.random.randn(n_points, 2) * 5  # Small motion
    descriptors1 = np.random.rand(n_points, 128).astype(np.float32)
    descriptors2 = np.random.rand(n_points, 128).astype(np.float32)
    
    data = {
        "coords1": coords_frame1,
        "coords2": coords_frame2,
        "descriptors1": descriptors1,
        "descriptors2": descriptors2
    }
    
    np.save(seq_dir / "correspondences.npy", data)
    
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_load_correspondences(temp_correspondences_dir):
    """Test loading correspondence data."""
    seq_path = Path(temp_correspondences_dir) / "Static-High" / "seq_001"
    coords1, coords2, descs1, descs2 = load_correspondences(seq_path)
    
    assert coords1.shape == (100, 2)
    assert coords2.shape == (100, 2)
    assert descs1.shape == (100, 128)
    assert descs2.shape == (100, 128)

def test_compute_fundamental_matrix():
    """Test fundamental matrix computation."""
    set_global_seed(42)
    # Create synthetic correspondences
    n_points = 100
    coords1 = np.random.rand(n_points, 2) * 200
    # True fundamental matrix (simplified)
    F_true = np.array([
        [0, 0, 1],
        [0, 0, -1],
        [-1, 1, 0]
    ], dtype=np.float32)
    
    # Generate corresponding points
    coords2 = []
    for p1 in coords1:
        x1, y1 = p1
        # Apply epipolar constraint: p2^T * F * p1 = 0
        # Simplified: just add noise
        x2 = x1 + np.random.randn() * 2
        y2 = y1 + np.random.randn() * 2
        coords2.append([x2, y2])
    coords2 = np.array(coords2)
    
    F, inliers = compute_fundamental_matrix(coords1, coords2)
    
    assert F.shape == (3, 3)
    assert inliers is not None
    assert len(inliers) > 0
    # Check that F is rank 2 (singular)
    assert np.linalg.matrix_rank(F) <= 2

def test_triangulate_points():
    """Test 3D point triangulation."""
    set_global_seed(42)
    n_points = 50
    coords1 = np.random.rand(n_points, 2) * 200
    coords2 = coords1 + np.random.randn(n_points, 2) * 5
    F = np.eye(3)
    F[0, 2] = -100
    F[1, 2] = -100
    
    points_3d = triangulate_points(coords1, coords2, F)
    
    assert points_3d.shape[1] == 3  # 3D points
    assert points_3d.shape[0] == n_points

def test_validate_reprojection_error():
    """Test reprojection error validation."""
    set_global_seed(42)
    n_points = 50
    coords1 = np.random.rand(n_points, 2) * 200
    coords2 = coords1 + np.random.randn(n_points, 2) * 5
    F = np.eye(3)
    F[0, 2] = -100
    F[1, 2] = -100
    
    error, passed = validate_reprojection_error(coords1, coords2, F)
    
    assert error >= 0
    assert isinstance(passed, bool)

def test_process_sequence(temp_correspondences_dir, temp_output_dir):
    """Test full sequence processing for the solver."""
    set_global_seed(42)
    seq_path = Path(temp_correspondences_dir) / "Static-High" / "seq_001"
    output_path = Path(temp_output_dir) / "seq_001"
    output_path.mkdir(parents=True, exist_ok=True)
    
    result = process_sequence(seq_path, output_path)
    
    # Result should be a dict or True
    assert result is not None
    
    if isinstance(result, dict):
        assert "fundamental_matrix" in result
        assert "points_3d" in result
        assert "inliers" in result
