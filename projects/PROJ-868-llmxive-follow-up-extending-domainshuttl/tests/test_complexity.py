"""
Tests for visual complexity scoring module.
"""
import os
import tempfile
import numpy as np
import cv2
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.data.complexity import (
    _load_frame_from_video,
    _compute_sobel_magnitude,
    compute_complexity_scores
)


def test_sobel_magnitude_on_edge():
    """Test Sobel magnitude calculation on a simple edge image."""
    # Create a simple image with a vertical edge
    frame = np.zeros((100, 100), dtype=np.uint8)
    frame[:, 50:] = 255  # Right half white
    
    # Convert to BGR (3 channels)
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    magnitude = _compute_sobel_magnitude(frame_bgr)
    
    # Should have a non-zero magnitude due to the edge
    assert magnitude > 0, "Edge detection should yield non-zero magnitude"


def test_sobel_magnitude_on_uniform():
    """Test Sobel magnitude on a uniform image (should be near zero)."""
    # Create a uniform image
    frame = np.ones((100, 100), dtype=np.uint8) * 128
    
    # Convert to BGR
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    magnitude = _compute_sobel_magnitude(frame_bgr)
    
    # Should be very close to zero (allow for floating point errors)
    assert magnitude < 1.0, "Uniform image should have near-zero magnitude"


def test_load_frame_from_video():
    """Test loading a specific frame from a video file."""
    # Create a temporary video file for testing
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        video_path = tmp.name
    
    try:
        # Create a simple video with known frames
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 10.0, (100, 100))
        
        # Write 10 frames with different values
        for i in range(10):
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            frame[:, :, 0] = i * 25  # Vary blue channel
            out.write(frame)
        
        out.release()
        
        # Test loading frame 5
        frame = _load_frame_from_video(video_path, 5, 10)
        assert frame is not None, "Frame should be loaded"
        assert frame.shape == (100, 100, 3), "Frame shape should be correct"
        # Check that the blue channel is approximately 5 * 25 = 125
        assert 120 < frame[0, 0, 0] < 130, "Frame content should match expected value"
        
    finally:
        if os.path.exists(video_path):
            os.unlink(video_path)


@patch('src.data.complexity.load_dataset')
@patch('src.data.complexity.ensure_dir')
def test_compute_complexity_scores(mock_ensure_dir, mock_load_dataset):
    """Test the main complexity scoring function with mocked dataset."""
    # Mock dataset items
    mock_items = [
        {'videoid': f'video_{i}', 'category': 'cat1', 'path': f'/fake/path_{i}.mp4'}
        for i in range(10)
    ]
    
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter(mock_items))
    mock_load_dataset.return_value = mock_dataset
    
    # Mock cv2.VideoCapture to return a fake video with known properties
    with patch('src.data.complexity.cv2.VideoCapture') as mock_cap:
        mock_cap_instance = MagicMock()
        mock_cap.return_value = mock_cap_instance
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.return_value = 100  # 100 frames
        mock_cap_instance.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
        mock_cap_instance.release = MagicMock()
        
        # Mock os.path.exists to return True for all paths
        with patch('src.data.complexity.os.path.exists', return_value=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, 'complexity_scores.csv')
                
                # Run the function
                result_df = compute_complexity_scores(
                    num_subjects=10,
                    frames_per_subject=5,
                    output_path=output_path
                )
                
                # Check that the output file was created
                assert os.path.exists(output_path), "Output CSV should be created"
                
                # Check the dataframe
                assert result_df is not None, "Result dataframe should not be None"
                assert 'subject_id' in result_df.columns, "subject_id column should exist"
                assert 'normalized_complexity_score' in result_df.columns, "normalized_complexity_score column should exist"
                assert len(result_df) == 10, "Should have 10 rows"
                
                # Check that scores are normalized (sum of squares should be 1)
                scores = result_df['normalized_complexity_score'].values
                l2_norm = np.linalg.norm(scores)
                assert abs(l2_norm - 1.0) < 1e-5, "Scores should be L2 normalized"