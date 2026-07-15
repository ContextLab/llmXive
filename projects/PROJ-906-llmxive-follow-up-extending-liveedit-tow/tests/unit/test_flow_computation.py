"""
Unit tests for optical flow computation (T009).
"""
import os
import tempfile
import numpy as np
import cv2
import pytest
from pathlib import Path

# Import the module under test
# We need to adjust the import path to match the project structure
# Assuming the test is run from the project root
import sys
sys.path.insert(0, 'code')

from data.flow import compute_farneback_flow, process_video_flow

def create_test_video(path: str, frames: int = 5, width: int = 128, height: int = 128):
    """Helper to create a synthetic test video."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, 10.0, (width, height))
    
    for i in range(frames):
        # Create a moving square
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        x = (i * 10) % (width - 20)
        cv2.rectangle(frame, (x, x), (x + 20, x + 20), (255, 255, 255), -1)
        out.write(frame)
    
    out.release()

def test_farneback_flow_computation():
    """Test that Farneback flow computes a non-zero field for moving objects."""
    # Create two frames with a moving object
    frame1 = np.zeros((100, 100), dtype=np.uint8)
    cv2.circle(frame1, (20, 20), 10, 255, -1)
    
    frame2 = np.zeros((100, 100), dtype=np.uint8)
    cv2.circle(frame2, (30, 20), 10, 255, -1) # Moved right by 10 pixels
    
    flow = compute_farneback_flow(frame1, frame2)
    
    assert flow.shape == (100, 100, 2)
    assert flow.dtype == np.float32
    
    # Check that there is significant flow in the region of the circle
    # The flow should be approximately (10, 0) in that region
    # We check the mean flow in the center area
    center_region = flow[15:25, 15:25]
    mean_flow_x = np.mean(center_region[..., 0])
    
    # The flow should be positive (moving right)
    assert mean_flow_x > 0.5, f"Expected positive flow, got {mean_flow_x}"

def test_process_video_flow(tmp_path):
    """Test the full video processing pipeline."""
    video_path = tmp_path / "test_video.mp4"
    output_dir = tmp_path / "flow_output"
    
    create_test_video(str(video_path), frames=5)
    
    result = process_video_flow(str(video_path), str(output_dir))
    
    assert result["total_frames"] == 5
    assert result["frames_processed"] == 4 # 4 flow fields for 5 frames
    assert len(result["flow_files"]) == 4
    assert os.path.exists(result["flow_files"][0])
    
    # Check statistics
    for stats in result["statistics"]:
        assert "mean_magnitude" in stats
        assert "max_magnitude" in stats
        assert "frame_idx" in stats

def test_flow_file_format(tmp_path):
    """Verify that saved flow files are valid numpy arrays."""
    video_path = tmp_path / "test_video.mp4"
    output_dir = tmp_path / "flow_output"
    
    create_test_video(str(video_path), frames=3)
    
    result = process_video_flow(str(video_path), str(output_dir))
    
    for flow_file in result["flow_files"]:
        assert os.path.exists(flow_file)
        flow_data = np.load(flow_file)
        assert flow_data.shape[2] == 2 # U, V channels
        assert flow_data.dtype == np.float32
        assert np.all(np.isfinite(flow_data)) # No NaN/Inf in valid flow