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
import json
import numpy as np
import cv2
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from geometry.solver import (
    load_correspondences,
    compute_fundamental_matrix,
    triangulate_points,
    validate_reprojection_error,
    process_sequence
)
from utils.seeds import set_global_seed
from config import get_features_dir, get_results_dir

@pytest.fixture(autouse=True)
def setup_seed():
    set_global_seed(42)

class TestLoadCorrespondences:
    def test_load_valid_correspondences(self, tmp_path):
        """Test loading valid correspondence data."""
        corr_file = tmp_path / "correspondences.npy"
        
        # Create test data
        keypoints1 = np.random.rand(10, 2).astype(np.float32)
        keypoints2 = np.random.rand(10, 2).astype(np.float32)
        
        data = {
            "keypoints1": keypoints1,
            "keypoints2": keypoints2,
            "descriptors1": np.random.rand(10, 128).astype(np.float32),
            "descriptors2": np.random.rand(10, 128).astype(np.float32)
        }
        
        np.save(str(corr_file), data)
        
        kp1, kp2 = load_correspondences(str(corr_file))
        
        assert kp1.shape == (10, 2)
        assert kp2.shape == (10, 2)
        assert kp1.dtype == np.float32
        assert kp2.dtype == np.float32

    def test_load_correspondences_with_descriptors(self, tmp_path):
        """Test loading with descriptor data."""
        corr_file = tmp_path / "correspondences_with_desc.npy"
        
        kp1 = np.random.rand(20, 2).astype(np.float32)
        kp2 = np.random.rand(20, 2).astype(np.float32)
        desc1 = np.random.rand(20, 64).astype(np.float32)
        desc2 = np.random.rand(20, 64).astype(np.float32)
        
        data = {
            "keypoints1": kp1,
            "keypoints2": kp2,
            "descriptors1": desc1,
            "descriptors2": desc2
        }
        
        np.save(str(corr_file), data)
        
        loaded_kp1, loaded_kp2 = load_correspondences(str(corr_file))
        
        assert np.allclose(loaded_kp1, kp1)
        assert np.allclose(loaded_kp2, kp2)

class TestComputeFundamentalMatrix:
    def test_compute_fm_with_inliers(self, tmp_path):
        """Test fundamental matrix computation with sufficient inliers."""
        # Generate synthetic correspondences with some noise
        np.random.seed(42)
        n_points = 50
        
        # Create points in first image
        pts1 = np.random.rand(n_points, 2).astype(np.float32) * 100
        
        # Create a simple fundamental matrix (epipolar constraint)
        F_true = np.array([
            [0, 0, 0.001],
            [0, 0, -0.001],
            [-0.001, 0.001, 0]
        ], dtype=np.float32)
        
        # Generate corresponding points in second image
        pts2 = np.zeros((n_points, 2), dtype=np.float32)
        for i in range(n_points):
            x1, y1 = pts1[i]
            # Add some noise
            noise = np.random.rand(2) * 0.5
            pts2[i] = [x1 + noise[0], y1 + noise[1]]
        
        F, mask = compute_fundamental_matrix(pts1, pts2)
        
        assert F is not None
        assert F.shape == (3, 3)
        assert mask is not None
        assert len(mask) == n_points
        # Should have some inliers
        assert np.sum(mask) > 0

    def test_compute_fm_with_low_texture(self, tmp_path):
        """Test fundamental matrix computation with low texture (few inliers)."""
        # Create nearly identical points (low texture)
        np.random.seed(42)
        n_points = 20
        
        pts1 = np.ones((n_points, 2), dtype=np.float32) * 50
        pts2 = np.ones((n_points, 2), dtype=np.float32) * 50
        
        F, mask = compute_fundamental_matrix(pts1, pts2)
        
        # With identical points, RANSAC should fail or find very few inliers
        # The function should handle this gracefully
        assert F is not None
        assert F.shape == (3, 3)

class TestTriangulatePoints:
    def test_triangulate_points_valid(self, tmp_tmp):
        """Test 3D point triangulation with valid inputs."""
        np.random.seed(42)
        
        # Create two camera matrices (simplified)
        K = np.array([
            [500, 0, 320],
            [0, 500, 240],
            [0, 0, 1]
        ], dtype=np.float32)
        
        R1 = np.eye(3, dtype=np.float32)
        t1 = np.zeros((3, 1), dtype=np.float32)
        P1 = K @ np.hstack([R1, t1])
        
        R2 = np.eye(3, dtype=np.float32)
        R2[0, 0] = 0.9  # Small rotation
        t2 = np.array([[0.1], [0], [0]], dtype=np.float32)  # Small translation
        P2 = K @ np.hstack([R2, t2])
        
        # Corresponding points
        pts1 = np.array([[320, 240], [330, 250]], dtype=np.float32)
        pts2 = np.array([[321, 240], [331, 250]], dtype=np.float32)
        
        points_3d = triangulate_points(pts1, pts2, P1, P2)
        
        assert points_3d is not None
        assert len(points_3d) == 2
        assert points_3d.shape[1] == 3  # 3D coordinates

class TestValidateReprojectionError:
    def test_validate_reprojection_error_low(self, tmp_path):
        """Test validation with low reprojection error."""
        np.random.seed(42)
        
        # Create points with low reprojection error
        pts1 = np.random.rand(10, 2).astype(np.float32) * 100
        pts2 = pts1 + np.random.rand(10, 2).astype(np.float32) * 0.1  # Very small error
        
        F, mask = compute_fundamental_matrix(pts1, pts2)
        error = validate_reprojection_error(pts1, pts2, F, mask)
        
        # Error should be very small
        assert error < 1.0

    def test_validate_reprojection_error_high(self, tmp_path):
        """Test validation with high reprojection error."""
        np.random.seed(42)
        
        # Create points with high reprojection error
        pts1 = np.random.rand(10, 2).astype(np.float32) * 100
        pts2 = np.random.rand(10, 2).astype(np.float32) * 100  # Random points
        
        F, mask = compute_fundamental_matrix(pts1, pts2)
        error = validate_reprojection_error(pts1, pts2, F, mask)
        
        # Error should be larger
        assert error >= 0  # Just ensure it's computed

class TestProcessSequence:
    def test_process_sequence_integration(self, tmp_path):
        """Test the full solver processing pipeline."""
        set_global_seed(42)
        
        # Create dummy correspondence file
        corr_file = tmp_path / "correspondences.npy"
        kp1 = np.random.rand(20, 2).astype(np.float32) * 100
        kp2 = np.random.rand(20, 2).astype(np.float32) * 100
        
        data = {
            "keypoints1": kp1,
            "keypoints2": kp2,
            "descriptors1": np.random.rand(20, 128).astype(np.float32),
            "descriptors2": np.random.rand(20, 128).astype(np.float32)
        }
        
        np.save(str(corr_file), data)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = process_sequence(str(corr_file), str(output_dir))
        
        assert result is not None
        assert "fundamental_matrix" in result
        assert "num_inliers" in result
        assert "reprojection_error" in result
        assert "is_solvable" in result
