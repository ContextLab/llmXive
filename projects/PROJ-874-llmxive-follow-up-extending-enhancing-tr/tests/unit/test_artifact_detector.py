import os
import sys
import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.artifact_detector import detect_tearing_artifacts, scan_video_for_artifacts

class TestDetectTearingArtifacts:
    """Unit tests for tearing artifact detection"""

    def test_valid_frame_no_artifact(self):
        """Test that a valid frame with normal pixel values returns None"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detect_tearing_artifacts(frame, "test_video", 0)
        assert result is None

    def test_float_frame_out_of_range_low(self):
        """Test detection of float frame with values < 0"""
        frame = np.random.rand(480, 640, 3).astype(np.float32)
        frame[100, 100, :] = -0.5  # Invalid value
        result = detect_tearing_artifacts(frame, "test_video", 0)
        assert result is not None
        assert result['artifact_type'] == 'invalid_pixel_range'
        assert result['video_id'] == 'test_video'
        assert result['frame_idx'] == 0

    def test_float_frame_out_of_range_high(self):
        """Test detection of float frame with values > 255"""
        frame = np.random.rand(480, 640, 3).astype(np.float32) * 255
        frame[100, 100, :] = 300.0  # Invalid value
        result = detect_tearing_artifacts(frame, "test_video", 0)
        assert result is not None
        assert result['artifact_type'] == 'invalid_pixel_range'

    def test_horizontal_black_tearing(self):
        """Test detection of horizontal black tearing (consecutive black lines)"""
        frame = np.ones((480, 640), dtype=np.uint8) * 128  # Gray background
        # Create 15 consecutive black lines
        frame[200:215, :] = 0
        result = detect_tearing_artifacts(frame, "test_video", 5)
        assert result is not None
        assert result['artifact_type'] == 'horizontal_tearing'
        assert result['frame_idx'] == 5

    def test_horizontal_white_tearing(self):
        """Test detection of horizontal white tearing (consecutive white lines)"""
        frame = np.ones((480, 640), dtype=np.uint8) * 128  # Gray background
        # Create 12 consecutive white lines
        frame[300:312, :] = 255
        result = detect_tearing_artifacts(frame, "test_video", 10)
        assert result is not None
        assert result['artifact_type'] == 'horizontal_tearing'

    def test_no_tearing_with_isolated_black_pixels(self):
        """Test that isolated black pixels don't trigger tearing detection"""
        frame = np.ones((480, 640), dtype=np.uint8) * 128
        # Create isolated black pixels (not consecutive)
        frame[200, :] = 0
        frame[202, :] = 0
        frame[204, :] = 0
        result = detect_tearing_artifacts(frame, "test_video", 0)
        assert result is None

    def test_grayscale_frame(self):
        """Test artifact detection on grayscale frames"""
        frame = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        result = detect_tearing_artifacts(frame, "test_video", 0)
        assert result is None  # Valid frame

    def test_invalid_log_format(self):
        """Test that artifacts have correct log format"""
        frame = np.ones((480, 640), dtype=np.uint8) * 128
        frame[200:210, :] = 0  # Black lines
        result = detect_tearing_artifacts(frame, "video_123", 42)
        
        assert 'video_id' in result
        assert 'frame_idx' in result
        assert 'artifact_type' in result
        assert result['video_id'] == 'video_123'
        assert result['frame_idx'] == 42
        assert result['artifact_type'] in ['invalid_pixel_range', 'horizontal_tearing', 'nan_inf_detected']

class TestScanVideoForArtifacts:
    """Integration tests for video scanning"""

    @pytest.fixture
    def temp_video_with_artifact(self, tmp_path):
        """Create a temporary video file with known artifacts"""
        video_path = tmp_path / "test_artifact.mp4"
        
        # Create frames with artifacts
        out = cv2.VideoWriter(
            str(video_path),
            cv2.VideoWriter_fourcc(*'mp4v'),
            10,
            (640, 480)
        )
        
        # Normal frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
        
        # Frame with tearing (black lines)
        tear_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        tear_frame[200:210, :, :] = 0  # Black tearing
        out.write(tear_frame)
        
        # Another normal frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
        
        out.release()
        return str(video_path)

    def test_scan_video_finds_artifacts(self, temp_video_with_artifact):
        """Test that scanning a video finds the inserted artifacts"""
        artifacts = scan_video_for_artifacts(temp_video_with_artifact, "test_video")
        
        assert len(artifacts) == 1
        assert artifacts[0]['video_id'] == 'test_video'
        assert artifacts[0]['frame_idx'] == 1  # Second frame (0-indexed)
        assert artifacts[0]['artifact_type'] == 'horizontal_tearing'

    def test_scan_video_no_artifacts(self, tmp_path):
        """Test scanning a video with no artifacts"""
        video_path = tmp_path / "clean_video.mp4"
        
        out = cv2.VideoWriter(
            str(video_path),
            cv2.VideoWriter_fourcc(*'mp4v'),
            10,
            (640, 480)
        )
        
        for _ in range(5):
            frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
            out.write(frame)
        
        out.release()
        
        artifacts = scan_video_for_artifacts(str(video_path), "clean_video")
        assert len(artifacts) == 0

    def test_nonexistent_video_raises_error(self, tmp_path):
        """Test that scanning a non-existent video raises an error"""
        fake_path = str(tmp_path / "nonexistent.mp4")
        
        with pytest.raises(Exception):
            scan_video_for_artifacts(fake_path, "test")