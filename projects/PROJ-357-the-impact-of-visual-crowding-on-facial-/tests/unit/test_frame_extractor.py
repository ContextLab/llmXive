import pytest
from pathlib import Path
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
import cv2
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.frame_extractor import extract_frames_from_video, extract_frames_from_dataset

class TestFrameExtractor:
    """Unit tests for frame extraction logic."""

    def test_extract_frames_creates_output(self, tmp_path):
        """Test that frames are actually written to disk."""
        # Create a dummy video file using OpenCV
        video_path = tmp_path / "test_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 1.0, (640, 480))
        
        # Write 5 dummy frames
        for _ in range(5):
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            out.write(frame)
        out.release()

        output_dir = tmp_path / "output"
        
        result = extract_frames_from_video(
            video_path=video_path,
            output_dir=output_dir
        )

        # Verify output directory exists
        assert output_dir.exists()
        
        # Verify frames were written
        frame_files = list(output_dir.glob("frame_*.jpg"))
        assert len(frame_files) == 5
        
        # Verify manifest content
        assert result["total_frames"] == 5
        assert result["videos_processed"] == 1
        assert result["video_path"] == str(video_path)

    def test_extract_frames_handles_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing video."""
        with pytest.raises(FileNotFoundError):
            extract_frames_from_video(
                video_path=Path("/nonexistent/video.mp4"),
                output_dir=tmp_path / "output"
            )

    def test_extract_frames_directory_creation(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "new_subdir" / "frames"
        assert not output_dir.exists()
        
        # Create a dummy video
        video_path = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 1.0, (640, 480))
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        # This should create the output_dir before writing frames
        extract_frames_from_video(
            video_path=video_path,
            output_dir=output_dir
        )

        assert output_dir.exists()

    def test_extract_frames_from_dataset_empty_dir(self, tmp_path):
        """Test handling of empty directory."""
        output_dir = tmp_path / "output"
        manifest = extract_frames_from_dataset(
            raw_data_dir=tmp_path,
            output_dir=output_dir,
            file_pattern="*.mp4"
        )
        
        assert manifest["total_frames"] == 0
        assert manifest["videos_processed"] == 0
        assert "files" in manifest
        assert "errors" in manifest
        assert isinstance(manifest["files"], list)
        assert isinstance(manifest["errors"], list)

    def test_extract_frames_manifest_structure(self, tmp_path):
        """Test that the manifest has the expected keys."""
        output_dir = tmp_path / "output"
        manifest = extract_frames_from_dataset(
            raw_data_dir=tmp_path,
            output_dir=output_dir,
            file_pattern="*.mp4"
        )
        
        expected_keys = ["files", "total_frames", "videos_processed", "errors"]
        for key in expected_keys:
            assert key in manifest

    def test_extract_frames_from_dataset_with_videos(self, tmp_path):
        """Test processing multiple videos in a directory."""
        # Create 2 dummy videos
        for i in range(2):
            video_path = tmp_path / f"video_{i}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(video_path), fourcc, 1.0, (640, 480))
            for _ in range(3):  # 3 frames each
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                out.write(frame)
            out.release()

        output_dir = tmp_path / "output"
        manifest = extract_frames_from_dataset(
            raw_data_dir=tmp_path,
            output_dir=output_dir,
            file_pattern="*.mp4"
        )

        assert manifest["videos_processed"] == 2
        assert manifest["total_frames"] == 6
        
        # Check that all frames exist
        frame_files = list(output_dir.glob("frame_*.jpg"))
        assert len(frame_files) == 6

    def test_extract_frames_with_corrupted_video(self, tmp_path):
        """Test handling of a corrupted video file."""
        # Create a corrupted video file (just random bytes)
        corrupted_path = tmp_path / "corrupted.mp4"
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not a valid video file")

        output_dir = tmp_path / "output"
        manifest = extract_frames_from_dataset(
            raw_data_dir=tmp_path,
            output_dir=output_dir,
            file_pattern="*.mp4"
        )

        # Should have processed 0 videos due to error
        assert manifest["videos_processed"] == 0
        assert len(manifest["errors"]) >= 1
        assert any("corrupted.mp4" in error for error in manifest["errors"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])