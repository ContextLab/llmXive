"""
Unit tests for video utility functions.

Tests for:
- Frame extraction logic
- Video metadata handling
- Frame writing/reading consistency
- Resize operations
"""
import pytest
import os
import sys
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.video import (
    get_video_metadata,
    extract_frames,
    extract_frames_to_list,
    write_video,
    extract_frames_from_directory,
    resize_frames,
    get_frame_at_time
)


class TestVideoMetadata:
    """Tests for video metadata extraction."""

    def test_get_video_metadata_mock(self):
        """Test metadata extraction with mocked video."""
        # Mock VideoCapture to avoid needing real file
        mock_capture = MagicMock()
        mock_capture.get.return_value = 30.0  # FPS
        mock_capture.get.return_value = 640  # Width
        mock_capture.get.return_value = 480  # Height
        mock_capture.get.return_value = 100  # Total frames (property 7)
        mock_capture.isOpened.return_value = True
        mock_capture.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        
        with patch('cv2.VideoCapture', return_value=mock_capture):
            # This test verifies the function doesn't crash and returns dict
            # Actual values depend on mock setup
            metadata = get_video_metadata("dummy_video.mp4")
            
            assert isinstance(metadata, dict), "Metadata should be a dictionary"
            assert "fps" in metadata, "Metadata should contain FPS"
            assert "width" in metadata, "Metadata should contain width"
            assert "height" in metadata, "Metadata should contain height"


class TestFrameExtraction:
    """Tests for frame extraction logic."""

    def test_extract_frames_to_list_count(self):
        """Test that frame extraction returns correct number of frames."""
        # Create mock frames
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        
        mock_capture = MagicMock()
        mock_capture.isOpened.return_value = True
        mock_capture.read.side_effect = [(True, f) for f in mock_frames] + [(False, None)] * 5
        mock_capture.get.return_value = 30.0
        
        with patch('cv2.VideoCapture', return_value=mock_capture):
            frames = extract_frames_to_list("dummy_video.mp4")
            
            assert len(frames) == 10, f"Expected 10 frames, got {len(frames)}"
            assert all(isinstance(f, np.ndarray) for f in frames), "All items should be arrays"

    def test_extract_frames_to_list_empty(self):
        """Test extraction from empty video."""
        mock_capture = MagicMock()
        mock_capture.isOpened.return_value = True
        mock_capture.read.return_value = (False, None)
        
        with patch('cv2.VideoCapture', return_value=mock_capture):
            frames = extract_frames_to_list("empty_video.mp4")
            assert len(frames) == 0, "Empty video should yield 0 frames"


class TestFrameWriting:
    """Tests for video writing logic."""

    def test_write_video_mock(self):
        """Test video writing with mocked writer."""
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(5)]
        
        mock_writer = MagicMock()
        mock_writer.isOpened.return_value = True
        
        with patch('cv2.VideoWriter', return_value=mock_writer):
            success = write_video("output.mp4", frames, 30.0)
            
            assert success is True, "Writing should succeed with mocked writer"
            assert mock_writer.write.call_count == 5, "Should write 5 frames"

    def test_write_video_invalid_frames(self):
        """Test handling of invalid frame types."""
        # Test with non-array frames
        frames = ["invalid", "frames"]
        
        with patch('cv2.VideoWriter') as mock_writer:
            # Should handle gracefully or raise appropriate error
            # For this test, we expect it to not crash on type check
            try:
                write_video("output.mp4", frames, 30.0)
            except (TypeError, ValueError):
                pass  # Expected for invalid input


class TestFrameResizing:
    """Tests for frame resizing operations."""

    def test_resize_frames_uniform(self):
        """Test resizing a list of frames."""
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
        target_size = (320, 240)
        
        resized = resize_frames(frames, target_size)
        
        assert len(resized) == 3, "Should preserve frame count"
        assert resized[0].shape[0] == target_size[1], "Height should match"
        assert resized[0].shape[1] == target_size[0], "Width should match"

    def test_resize_frames_empty_list(self):
        """Test resizing empty list."""
        resized = resize_frames([], (320, 240))
        assert len(resized) == 0, "Empty input should yield empty output"


class TestFrameAtTime:
    """Tests for frame retrieval at specific time."""

    def test_get_frame_at_time_mock(self):
        """Test frame retrieval at specific time."""
        mock_capture = MagicMock()
        mock_capture.isOpened.return_value = True
        mock_capture.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_capture.get.return_value = 30.0  # FPS
        
        with patch('cv2.VideoCapture', return_value=mock_capture):
            frame = get_frame_at_time("dummy_video.mp4", 2.0)
            
            assert isinstance(frame, np.ndarray), "Should return numpy array"
            assert frame.shape == (480, 640, 3), "Frame shape should match"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
