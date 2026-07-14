"""
Unit tests for code/data/extract_features.py
Tests cover:
- SIFT/ORB descriptor extraction
- Fast sequence detection logic
- Coordinate validity
"""
import os
import sys
import tempfile
import cv2
import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.extract_features import extract_sparse_features, is_fast_sequence, load_sequence_frames

@pytest.fixture
def sample_frames():
    """Create a small set of synthetic video frames for testing."""
    frames = []
    for i in range(5):
        # Create a frame with a moving circle
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        center = (50 + i * 5, 50)
        cv2.circle(frame, center, 10, (255, 255, 255), -1)
        frames.append(frame)
    return frames

@pytest.fixture
def sample_fast_frames():
    """Create frames with high motion (fast sequence)."""
    frames = []
    for i in range(5):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        # Rapidly moving object
        center = (50 + i * 20, 50)
        cv2.circle(frame, center, 10, (255, 255, 255), -1)
        frames.append(frame)
    return frames

def test_extract_sparse_features_sift(sample_frames):
    """Test SIFT descriptor extraction returns valid data."""
    descriptors, keypoints = extract_sparse_features(sample_frames, method='sift')
    
    # Check types
    assert isinstance(descriptors, np.ndarray)
    assert isinstance(keypoints, list)
    
    # Check non-empty if texture exists
    if len(sample_frames) > 0:
        assert len(keypoints) > 0, "Should find keypoints in synthetic frames"
        # Descriptors should match keypoints count
        assert len(descriptors) == len(keypoints), "Descriptor count must match keypoint count"
        
        # Check descriptor shape (SIFT typically 128-d)
        if len(descriptors) > 0:
            assert descriptors.shape[1] == 128, "SIFT descriptors should be 128-dimensional"

def test_extract_sparse_features_orb(sample_frames):
    """Test ORB descriptor extraction returns valid data."""
    descriptors, keypoints = extract_sparse_features(sample_frames, method='orb')
    
    # Check types
    assert isinstance(descriptors, np.ndarray)
    assert isinstance(keypoints, list)
    
    # Check non-empty
    assert len(keypoints) > 0, "Should find keypoints in synthetic frames"
    assert len(descriptors) == len(keypoints), "Descriptor count must match keypoint count"
    
    # ORB descriptors are typically 32 bytes (256 bits)
    if len(descriptors) > 0:
        assert descriptors.shape[1] == 32, "ORB descriptors should be 32-byte"

def test_is_fast_sequence_low_motion(sample_frames):
    """Test that low motion sequences are NOT flagged as fast."""
    assert not is_fast_sequence(sample_frames), "Static/slow sequence should not be flagged as fast"

def test_is_fast_sequence_high_motion(sample_fast_frames):
    """Test that high motion sequences ARE flagged as fast."""
    assert is_fast_sequence(sample_fast_frames), "Fast moving sequence should be flagged as fast"

def test_load_sequence_frames_invalid_path():
    """Test loading frames from non-existent path raises error."""
    with pytest.raises(FileNotFoundError):
        load_sequence_frames("/nonexistent/path/to/video.mp4")

def test_extract_features_empty_frame_list():
    """Test extraction on empty list returns empty arrays."""
    descriptors, keypoints = extract_sparse_features([], method='sift')
    assert len(keypoints) == 0
    assert len(descriptors) == 0

def test_extract_features_invalid_method(sample_frames):
    """Test extraction with invalid method raises error."""
    with pytest.raises(ValueError):
        extract_sparse_features(sample_frames, method='invalid_method')
