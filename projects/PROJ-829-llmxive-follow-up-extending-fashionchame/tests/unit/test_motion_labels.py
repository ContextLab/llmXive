"""
Unit tests for motion_labels.py (T044).
Tests optical flow computation and chunked processing logic.
"""
import pytest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import numpy as np
import cv2

# Import the module under test
from src.stats.motion_labels import (
    compute_optical_flow_magnitude,
    generate_motion_labels_chunked,
    run_pipeline,
    OPTICAL_FLOW_THRESHOLD
)


class TestOpticalFlowComputation:
    """Tests for compute_optical_flow_magnitude function."""

    def test_compute_optical_flow_magnitude_shapes(self):
        """Test that the output shape matches input shape."""
        # Create dummy grayscale frames
        prev_frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        next_frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        mag_map = compute_optical_flow_magnitude(prev_frame, next_frame)

        assert mag_map.shape == (100, 100)
        assert mag_map.dtype == np.float32  # OpenCV usually returns float32

    def test_compute_optical_flow_magnitude_static_frame(self):
        """Test that static frame (no motion) yields near-zero magnitude."""
        frame = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        
        mag_map = compute_optical_flow_magnitude(frame, frame)
        
        mean_mag = np.mean(mag_map)
        # Should be very small, but not exactly zero due to float precision
        assert mean_mag < 1.0

    def test_compute_optical_flow_magnitude_none_input(self):
        """Test that None input raises ValueError."""
        with pytest.raises(ValueError):
            compute_optical_flow_magnitude(None, np.zeros((10, 10)))
        
        with pytest.raises(ValueError):
            compute_optical_flow_magnitude(np.zeros((10, 10)), None)


class TestMotionLabelGeneration:
    """Tests for generate_motion_labels_chunked and related logic."""

    @patch('src.stats.motion_labels.load_frames_from_video_path')
    @patch('src.stats.motion_labels.compute_optical_flow_magnitude')
    def test_generate_motion_labels_chunked_subsampling(self, mock_flow, mock_load_frames):
        """Test that the generator respects subsampling ratio (every 5th frame)."""
        
        # Mock frames: 11 frames (indices 0..10)
        # With ratio 5, we should process pairs: (0, 5), (5, 10).
        # (0, 5) -> yields result for frame 0
        # (5, 10) -> yields result for frame 5
        # (10, 15) -> 15 doesn't exist, stop.
        
        mock_frames = [np.zeros((10, 10), dtype=np.uint8) for _ in range(11)]
        mock_load_frames.return_value = iter(mock_frames)
        
        # Mock flow magnitude to return a constant value
        mock_flow.return_value = np.ones((10, 10)) * 10.0  # High motion

        results = list(generate_motion_labels_chunked(
            video_path=Path("dummy.mp4"),
            chunk_size=10,
            subsampling_ratio=5
        ))

        # We expect 2 results: for frame 0 and frame 5
        assert len(results) == 2
        assert results[0]['frame_id'] == 0
        assert results[1]['frame_id'] == 5
        
        # Verify compute_optical_flow_magnitude was called with correct pairs
        # First call: (frame[0], frame[5])
        # Second call: (frame[5], frame[10])
        assert mock_flow.call_count == 2

    @patch('src.stats.motion_labels.load_frames_from_video_path')
    @patch('src.stats.motion_labels.compute_optical_flow_magnitude')
    def test_generate_motion_labels_chunked_threshold(self, mock_flow, mock_load_frames):
        """Test that motion labels are correctly assigned based on threshold."""
        
        mock_frames = [np.zeros((10, 10), dtype=np.uint8) for _ in range(6)]
        mock_load_frames.return_value = iter(mock_frames)
        
        # Mock flow to return different magnitudes
        # First pair (0, 5): High motion (10.0 > 5.0)
        # Second pair (5, 10): Wait, we only have 6 frames (0..5).
        # With ratio 5, pairs are (0, 5). Next is (5, 10) which doesn't exist.
        # So only 1 pair.
        
        mock_flow.side_effect = [
            np.ones((10, 10)) * 10.0, # High
            np.ones((10, 10)) * 2.0   # Low (if we had more frames)
        ]

        results = list(generate_motion_labels_chunked(
            video_path=Path("dummy.mp4"),
            chunk_size=10,
            subsampling_ratio=5
        ))

        assert len(results) == 1
        assert results[0]['motion_label'] == 'High'
        assert results[0]['optical_flow_magnitude'] == 10.0

    @patch('src.stats.motion_labels.load_frames_from_video_path')
    @patch('src.stats.motion_labels.compute_optical_flow_magnitude')
    def test_generate_motion_labels_chunked_oom_prevention(self, mock_flow, mock_load_frames):
        """Test that the generator yields results incrementally (generator behavior)."""
        
        mock_frames = [np.zeros((10, 10), dtype=np.uint8) for _ in range(100)]
        mock_load_frames.return_value = iter(mock_frames)
        mock_flow.return_value = np.ones((10, 10)) * 1.0

        gen = generate_motion_labels_chunked(
            video_path=Path("dummy.mp4"),
            chunk_size=2, # Small chunk size
            subsampling_ratio=5
        )

        # Verify it's a generator
        assert hasattr(gen, '__next__')
        
        # Consume first item
        first = next(gen)
        assert first is not None


class TestPipelineIntegration:
    """Integration tests for run_pipeline."""

    def test_run_pipeline_creates_output_file(self):
        """Test that run_pipeline creates the output JSON file."""
        # Create a temporary manifest
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            manifest_path = tmpdir_path / "manifest.json"
            output_path = tmpdir_path / "motion_labels.json"
            
            # Create a dummy manifest
            manifest_data = [
                {"video_path": str(tmpdir_path / "dummy.mp4")} # This file doesn't exist, but let's see how it handles
            ]
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f)
            
            # We expect it to skip the missing file and produce an empty list or handle gracefully
            # The current implementation skips missing files.
            result = run_pipeline(manifest_path, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 0 # No valid videos

    @patch('src.stats.motion_labels.load_frames_from_video_path')
    def test_run_pipeline_with_real_logic_mocked(self, mock_load_frames):
        """Test run_pipeline with mocked video reading to ensure flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            manifest_path = tmpdir_path / "manifest.json"
            output_path = tmpdir_path / "motion_labels.json"
            
            # Create a dummy video file (empty file is enough for existence check)
            dummy_video = tmpdir_path / "dummy.mp4"
            dummy_video.touch()
            
            manifest_data = [{"video_path": str(dummy_video)}]
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f)
            
            # Mock the frame loader to return a few frames
            mock_frames = [np.zeros((20, 20), dtype=np.uint8) for _ in range(6)]
            mock_load_frames.return_value = iter(mock_frames)
            
            result = run_pipeline(manifest_path, output_path)
            
            assert result['total_records'] == 1 # (0, 5) pair
            assert output_path.exists()