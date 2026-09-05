"""
Unit tests for SfM recovery logic in the DreamX-Lite pipeline.

This module verifies the correctness of:
1. COLMAP execution and parsing (success/failure detection)
2. Trajectory extraction from SfM outputs
3. Failure reason parsing and logging

Dependencies:
- code/pipeline/evaluate.py (extract_trajectory_from_sfm, parse_colmap_failure_reason)
- code/utils/config.py (ensure_directories)
"""
import os
import json
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

# Import from project modules
from pipeline.evaluate import (
    extract_trajectory_from_sfm,
    parse_colmap_failure_reason,
)
from utils.config import ensure_directories

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSfMRecovery:
    """Test suite for SfM recovery and trajectory extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        # Ensure required directories exist
        ensure_directories(self.project_root)

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_trajectory_from_sfm_success(self):
        """Test successful extraction of trajectory from valid SfM output."""
        # Create mock SfM output directory structure
        sfm_dir = self.project_root / "sfm_output"
        sfm_dir.mkdir()
        
        # Create cameras.txt
        cameras_path = sfm_dir / "cameras.txt"
        cameras_path.write_text(
            "# Camera list with one row of data per camera.\n"
            "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
            "1 PINHOLE 640 480 500.0 500.0 320.0 240.0\n"
        )
        
        # Create images.txt with valid camera poses
        images_path = sfm_dir / "images.txt"
        images_path.write_text(
            "# Image list with two lines of data per image.\n"
            "# IMAGE_ID, QW, QS, QX, QY, TX, TY, TZ, CAMERA_ID, NAME\n"
            "# POINTS2D[]s (X, Y, POINT3D_ID)\n"
            "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_0000.jpg\n"
            "0.0 0.0 -1.0\n"
            "2 0.707 0.0 0.0 0.707 1.0 0.0 0.0 1 frame_0001.jpg\n"
            "0.0 0.0 -1.0\n"
            "3 0.0 0.0 0.0 1.0 2.0 0.0 0.0 1 frame_0002.jpg\n"
            "0.0 0.0 -1.0\n"
        )
        
        # Create points3D.txt
        points3d_path = sfm_dir / "points3D.txt"
        points3d_path.write_text(
            "# 3D point list with one line of data per point.\n"
            "# POINT3D_ID, X, Y, Z, R, G, B, ERROR\n"
            "1 0.0 0.0 -5.0 255 0 0 0.0\n"
        )

        # Run extraction
        trajectory = extract_trajectory_from_sfm(sfm_dir)

        # Verify results
        assert trajectory is not None
        assert len(trajectory) == 3
        
        # Verify first frame pose (identity)
        assert np.allclose(trajectory[0]["R"], np.eye(3), atol=1e-5)
        assert np.allclose(trajectory[0]["T"], [0.0, 0.0, 0.0], atol=1e-5)
        
        # Verify second frame pose (rotation around Y)
        expected_R = np.array([[0.707, 0.0, 0.707], [0.0, 1.0, 0.0], [-0.707, 0.0, 0.707]])
        assert np.allclose(trajectory[1]["R"], expected_R, atol=1e-3)
        
        logger.info("Test passed: Successful trajectory extraction")

    def test_extract_trajectory_from_sfm_empty_images(self):
        """Test handling of empty images.txt file."""
        sfm_dir = self.project_root / "sfm_empty"
        sfm_dir.mkdir()
        
        # Create empty images.txt
        (sfm_dir / "images.txt").write_text(
            "# Image list\n"
            "# IMAGE_ID, QW, QS, QX, QY, TX, TY, TZ, CAMERA_ID, NAME\n"
        )
        
        (sfm_dir / "cameras.txt").write_text(
            "# Camera list\n"
            "1 PINHOLE 640 480 500.0 500.0 320.0 240.0\n"
        )
        
        (sfm_dir / "points3D.txt").write_text(
            "# 3D point list\n"
        )

        # Run extraction - should return empty list
        trajectory = extract_trajectory_from_sfm(sfm_dir)

        assert trajectory == []
        logger.info("Test passed: Empty trajectory handling")

    def test_parse_colmap_failure_reason_insufficient_features(self):
        """Test parsing of 'insufficient_features' error."""
        log_content = (
            "INFO: Reconstruction started\n"
            "WARNING: Not enough matches found for image frame_0001.jpg\n"
            "ERROR: Insufficient features detected for bundle adjustment\n"
            "Process exited with code 1\n"
        )
        
        reason = parse_colmap_failure_reason(log_content)
        
        assert reason == "insufficient_features"
        logger.info("Test passed: Insufficient features parsing")

    def test_parse_colmap_failure_reason_optimization_divergence(self):
        """Test parsing of 'optimization_divergence' error."""
        log_content = (
            "INFO: Bundle adjustment started\n"
            "WARNING: Cost function increasing\n"
            "ERROR: Optimization diverged after 100 iterations\n"
            "Process exited with code 1\n"
        )
        
        reason = parse_colmap_failure_reason(log_content)
        
        assert reason == "optimization_divergence"
        logger.info("Test passed: Optimization divergence parsing")

    def test_parse_colmap_failure_reason_sparse_reconstruction(self):
        """Test parsing of 'sparse_reconstruction' error."""
        log_content = (
            "INFO: Starting sparse reconstruction\n"
            "ERROR: Sparse reconstruction failed - no common points\n"
            "Process exited with code 1\n"
        )
        
        reason = parse_colmap_failure_reason(log_content)
        
        assert reason == "sparse_reconstruction"
        logger.info("Test passed: Sparse reconstruction failure parsing")

    def test_parse_colmap_failure_reason_no_error(self):
        """Test parsing when no error is found."""
        log_content = (
            "INFO: Reconstruction completed successfully\n"
            "INFO: 100 points reconstructed\n"
            "INFO: 5 images processed\n"
        )
        
        reason = parse_colmap_failure_reason(log_content)
        
        assert reason == ""
        logger.info("Test passed: No error detection")

    def test_parse_colmap_failure_reason_unknown_error(self):
        """Test parsing of unknown error type."""
        log_content = (
            "INFO: Processing\n"
            "ERROR: Unknown error occurred\n"
        )
        
        reason = parse_colmap_failure_reason(log_content)
        
        assert reason == ""
        logger.info("Test passed: Unknown error handling")

    def test_extract_trajectory_with_corrupted_images_file(self):
        """Test handling of corrupted images.txt file."""
        sfm_dir = self.project_root / "sfm_corrupted"
        sfm_dir.mkdir()
        
        # Create corrupted images.txt (missing fields)
        (sfm_dir / "images.txt").write_text(
            "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_0000.jpg\n"
            "2 0.707 0.0 0.0 0.707 1.0 0.0 0.0 1 frame_0001.jpg\n"
        )
        
        (sfm_dir / "cameras.txt").write_text(
            "1 PINHOLE 640 480 500.0 500.0 320.0 240.0\n"
        )
        
        (sfm_dir / "points3D.txt").write_text("")

        # Should handle gracefully and return empty or partial data
        trajectory = extract_trajectory_from_sfm(sfm_dir)
        
        # Depending on implementation, might return empty or partial
        assert isinstance(trajectory, list)
        logger.info("Test passed: Corrupted file handling")

    def test_integration_mocked_colmap_run(self):
        """Integration test with mocked COLMAP subprocess."""
        sfm_dir = self.project_root / "sfm_integration"
        sfm_dir.mkdir()
        
        # Mock the COLMAP subprocess call
        with patch("pipeline.evaluate.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Reconstruction completed successfully",
                stderr=""
            )
            
            # Create minimal valid SfM output
            (sfm_dir / "images.txt").write_text(
                "1 1.0 0.0 0.0 0.0 0.0 0.0 0.0 1 frame_0000.jpg\n"
                "0.0 0.0 -1.0\n"
            )
            (sfm_dir / "cameras.txt").write_text(
                "1 PINHOLE 640 480 500.0 500.0 320.0 240.0\n"
            )
            (sfm_dir / "points3D.txt").write_text("")
            
            trajectory = extract_trajectory_from_sfm(sfm_dir)
            
            assert len(trajectory) == 1
            assert mock_run.called
            logger.info("Test passed: Mocked COLMAP integration")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])