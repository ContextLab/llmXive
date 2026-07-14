import os
import sys
import json
import numpy as np
import cv2
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.stratify import (
    calculate_optical_flow_magnitude,
    calculate_texture_entropy,
    load_sequence_frames,
    classify_sequence,
    stratify_dataset
)
from utils.seeds import set_global_seed

# Set seed for reproducibility
set_global_seed(42)

@pytest.fixture
def temp_sequence_dir(tmp_path):
    """Create a temporary directory with mock video frames."""
    seq_dir = tmp_path / "test_seq"
    seq_dir.mkdir()
    
    # Create 5 mock frames (100x100 grayscale)
    for i in range(5):
        frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        frame_path = seq_dir / f"frame_{i:04d}.png"
        cv2.imwrite(str(frame_path), frame)
    
    return seq_dir

def test_calculate_optical_flow_magnitude(temp_sequence_dir):
    """Test optical flow magnitude calculation."""
    frames = load_sequence_frames(str(temp_sequence_dir))
    
    magnitude = calculate_optical_flow_magnitude(frames)
    
    assert isinstance(magnitude, (int, float))
    assert magnitude >= 0

def test_calculate_texture_entropy(temp_sequence_dir):
    """Test texture entropy calculation."""
    frames = load_sequence_frames(str(temp_sequence_dir))
    
    entropy = calculate_texture_entropy(frames[0])
    
    assert isinstance(entropy, (int, float))
    assert entropy >= 0

def test_classify_sequence_static_high(temp_sequence_dir):
    """Test sequence classification for static-high texture."""
    # Create static frames with high texture
    static_frames = [np.random.randint(50, 200, (100, 100), dtype=np.uint8) for _ in range(5)]
    
    motion_magnitude = calculate_optical_flow_magnitude(static_frames)
    texture_entropy = calculate_texture_entropy(static_frames[0])
    
    classification = classify_sequence(motion_magnitude, texture_entropy)
    
    # Should be classified as Static (low motion)
    assert 'Static' in classification or 'Slow' in classification

def test_classify_sequence_fast_low(tmp_path):
    """Test sequence classification for fast-low texture."""
    # Create fast-moving frames with low texture
    fast_frames = []
    for i in range(5):
        # Low texture (mostly uniform)
        frame = np.ones((100, 100), dtype=np.uint8) * 128
        # Add motion by shifting
        frame[:, i*20:] = 200
        fast_frames.append(frame)
    
    motion_magnitude = calculate_optical_flow_magnitude(fast_frames)
    texture_entropy = calculate_texture_entropy(fast_frames[0])
    
    classification = classify_sequence(motion_magnitude, texture_entropy)
    
    # Should be classified as Fast (high motion)
    assert 'Fast' in classification

def test_stratify_dataset_min_sequences(tmp_path):
    """Test stratification with minimum sequence requirements."""
    # Create a mock dataset structure
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    # Create 200 mock sequences (enough for all strata)
    for i in range(200):
        seq_dir = raw_dir / f"seq_{i:04d}"
        seq_dir.mkdir()
        
        for j in range(5):
            frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
            cv2.imwrite(str(seq_dir / f"frame_{j:04d}.png"), frame)
    
    # Test stratification
    result = stratify_dataset(
        str(raw_dir),
        str(tmp_path / "stratified"),
        sequences_per_stratum=50
    )
    
    assert result is not None
    assert 'strata' in result
    assert len(result['strata']) == 4

def test_stratify_dataset_insufficient_sequences(tmp_path):
    """Test stratification with insufficient sequences."""
    # Create only 10 sequences total
    raw_dir = tmp_path / "raw_small"
    raw_dir.mkdir()
    
    for i in range(10):
        seq_dir = raw_dir / f"seq_{i:04d}"
        seq_dir.mkdir()
        
        for j in range(5):
            frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
            cv2.imwrite(str(seq_dir / f"frame_{j:04d}.png"), frame)
    
    # Should raise an error or return empty result
    with pytest.raises(ValueError, match="fewer than 50 sequences"):
        stratify_dataset(
            str(raw_dir),
            str(tmp_path / "stratified_small"),
            sequences_per_stratum=50
        )

def test_load_sequence_frames_order(temp_sequence_dir):
    """Test that frames are loaded in correct order."""
    frames = load_sequence_frames(str(temp_sequence_dir))
    
    # Check that frames are sorted correctly
    assert len(frames) == 5
    assert all(isinstance(f, np.ndarray) for f in frames)

def test_load_sequence_frames_invalid_format(tmp_path):
    """Test loading frames with invalid format."""
    # Create a directory with non-image files
    seq_dir = tmp_path / "invalid_seq"
    seq_dir.mkdir()
    
    (seq_dir / "frame_0000.txt").write_text("not an image")
    
    with pytest.raises(ValueError, match="No valid frames found"):
        load_sequence_frames(str(seq_dir))
