"""
Unit tests for optical flow extraction module.
"""
import os
import sys
import tempfile
import numpy as np
import cv2
import pytest
from pathlib import Path

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.extract_optical import (
    extract_optical_flow_features,
    extract_hog_density,
    process_video_clip,
    batch_process_clips
)

@pytest.fixture
def temp_video_dir():
    """Create a temporary directory with test videos."""
    temp_dir = tempfile.mkdtemp()
    
    # Create two simple test frames
    frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
    frame1[20:80, 20:80] = 255  # White square
    
    frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
    frame2[30:90, 30:90] = 255  # Moved white square
    
    # Save as test video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(os.path.join(temp_dir, 'test_video.mp4'), fourcc, 10.0, (100, 100))
    out.write(frame1)
    out.write(frame2)
    out.release()
    
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_optical_flow_basic(temp_video_dir):
    """Test basic optical flow extraction."""
    cap = cv2.VideoCapture(os.path.join(temp_video_dir, 'test_video.mp4'))
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    cap.release()
    
    assert ret, "Could not read frames"
    
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    mean_mag, var_mag = extract_optical_flow_features(gray1, gray2)
    
    assert isinstance(mean_mag, float)
    assert isinstance(var_mag, float)
    assert mean_mag >= 0
    assert var_mag >= 0

def test_hog_density_basic(temp_video_dir):
    """Test basic HOG density extraction."""
    cap = cv2.VideoCapture(os.path.join(temp_video_dir, 'test_video.mp4'))
    ret, frame = cap.read()
    cap.release()
    
    assert ret, "Could not read frame"
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    density = extract_hog_density(gray)
    
    assert isinstance(density, float)
    assert density >= 0

def test_process_video_clip(temp_video_dir):
    """Test full video clip processing."""
    video_path = os.path.join(temp_video_dir, 'test_video.mp4')
    
    result = process_video_clip(video_path, "test_clip_001", "test_dimension")
    
    assert result["clip_id"] == "test_clip_001"
    assert result["dimension"] == "test_dimension"
    assert result["missing_data_flag"] == False
    assert result["feature_vector"] != "NaN"
    
    # Verify feature vector format
    features = [float(x) for x in result["feature_vector"].split(",")]
    assert len(features) == 3  # mean_mag, var_mag, hog_density

def test_process_video_clip_missing_file():
    """Test processing a non-existent video file."""
    result = process_video_clip("/nonexistent/path.mp4", "test_clip_002", "test_dimension")
    
    assert result["clip_id"] == "test_clip_002"
    assert result["missing_data_flag"] == True
    assert result["feature_vector"] == "NaN"