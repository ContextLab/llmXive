"""
Unit tests for code/geometry/solver.py
Tests cover:
- Fundamental matrix computation
- RANSAC inlier validation
- Reprojection error calculation
- Handling of unsolvable sequences
"""
import os
import sys
import numpy as np
import cv2
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from geometry.solver import compute_fundamental_matrix, validate_reprojection_error, triangulate_points

@pytest.fixture
def good_correspondences():
    """Generate valid correspondences with some noise."""
    # Create synthetic 2D points in two views
    points1 = np.array([
        [10.0, 10.0], [20.0, 20.0], [30.0, 30.0],
        [100.0, 50.0], [150.0, 100.0], [200.0, 150.0]
    ], dtype=np.float64)
    
    # Transform points (simulating epipolar geometry)
    # Simple translation and slight rotation
    points2 = np.array([
        [15.0, 12.0], [25.0, 22.0], [35.0, 32.0],
        [105.0, 52.0], [155.0, 102.0], [205.0, 152.0]
    ], dtype=np.float64)
    
    return points1, points2

@pytest.fixture
def bad_correspondences():
    """Generate correspondences with too few points for RANSAC."""
    points1 = np.array([[10.0, 10.0]], dtype=np.float64)
    points2 = np.array([[15.0, 12.0]], dtype=np.float64)
    return points1, points2

@pytest.fixture
def collinear_correspondences():
    """Generate collinear points (should fail fundamental matrix estimation)."""
    points1 = np.array([
        [10.0, 10.0], [20.0, 20.0], [30.0, 30.0], [40.0, 40.0]
    ], dtype=np.float64)
    points2 = np.array([
        [15.0, 15.0], [25.0, 25.0], [35.0, 35.0], [45.0, 45.0]
    ], dtype=np.float64)
    return points1, points2

def test_compute_fundamental_matrix_valid(good_correspondences):
    """Test F-matrix computation with valid correspondences."""
    points1, points2 = good_correspondences
    F, mask = compute_fundamental_matrix(points1, points2)
    
    # Check F matrix shape
    assert F.shape == (3, 3), "Fundamental matrix must be 3x3"
    
    # Check for non-zero matrix
    assert not np.allclose(F, 0), "Fundamental matrix should not be zero"
    
    # Check mask has inliers
    assert np.sum(mask) >= 4, "RANSAC should find at least 4 inliers"

def test_compute_fundamental_matrix_insufficient_points(bad_correspondences):
    """Test F-matrix fails gracefully with too few points."""
    points1, points2 = bad_correspondences
    F, mask = compute_fundamental_matrix(points1, points2)
    
    # Should return None or zero matrix
    assert F is None or np.allclose(F, 0), "Should fail with insufficient points"

def test_compute_fundamental_matrix_collinear(collinear_correspondences):
    """Test F-matrix handling of collinear points."""
    points1, points2 = collinear_correspondences
    F, mask = compute_fundamental_matrix(points1, points2)
    
    # Collinear points are degenerate
    # Depending on OpenCV version, might return None or unstable matrix
    assert F is not None, "Function should handle collinear points without crashing"

def test_validate_reprojection_error_valid(good_correspondences):
    """Test reprojection error calculation with valid F-matrix."""
    points1, points2 = good_correspondences
    F, mask = compute_fundamental_matrix(points1, points2)
    
    if F is not None and np.sum(mask) > 0:
        error = validate_reprojection_error(points1, points2, F, mask)
        
        # Error should be a non-negative float
        assert isinstance(error, (int, float)), "Error should be numeric"
        assert error >= 0, "Reprojection error must be non-negative"
        assert not np.isnan(error), "Error should not be NaN"

def test_triangulate_points_valid(good_correspondences):
    """Test 3D point triangulation."""
    points1, points2 = good_correspondences
    F, mask = compute_fundamental_matrix(points1, points2)
    
    if F is not None and np.sum(mask) > 0:
        # Create dummy camera matrices (identity + translation)
        K = np.eye(3)
        R1, t1 = np.eye(3), np.zeros((3,))
        R2, t2 = np.eye(3), np.array([1.0, 0.0, 0.0])
        
        P1 = K @ np.hstack((R1, t1.reshape(-1, 1)))
        P2 = K @ np.hstack((R2, t2.reshape(-1, 1)))
        
        # Select inliers
        inlier_pts1 = points1[mask.ravel()]
        inlier_pts2 = points2[mask.ravel()]
        
        points_3d = triangulate_points(inlier_pts1, inlier_pts2, P1, P2)
        
        assert points_3d is not None, "Triangulation should succeed"
        assert points_3d.shape[0] == len(inlier_pts1), "Should produce one 3D point per correspondence"
        assert points_3d.shape[1] == 3, "Points should be 3D"
        assert not np.any(np.isnan(points_3d)), "Triangulated points should not contain NaN"
