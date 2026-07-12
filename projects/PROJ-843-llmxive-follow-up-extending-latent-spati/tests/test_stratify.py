import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import cv2

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.stratify import (
    calculate_optical_flow_magnitude,
    calculate_texture_entropy,
    classify_sequence,
    MIN_SEQUENCE_PER_STRATUM
)
from config import get_stratified_dir, get_raw_dir, ensure_directories

def test_optical_flow_magnitude_static():
    """Test that static frames have near-zero motion magnitude."""
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frames = [frame, frame.copy()]
    magnitude = calculate_optical_flow_magnitude(frames)
    assert magnitude < 1.0, f"Static frames should have low motion, got {magnitude}"

def test_optical_flow_magnitude_moving():
    """Test that moving frames have higher motion magnitude."""
    frame1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    # Create frame2 with shifted content (simulating motion)
    frame2 = np.roll(frame1, shift=10, axis=1)
    frames = [frame1, frame2]
    magnitude = calculate_optical_flow_magnitude(frames)
    assert magnitude > 0.5, f"Moving frames should have higher motion, got {magnitude}"

def test_texture_entropy_low():
    """Test texture entropy for low-texture (uniform) images."""
    # Uniform image should have low entropy
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    frames = [frame]
    entropy = calculate_texture_entropy(frames)
    assert entropy < 0.1, f"Uniform image should have low entropy, got {entropy}"

def test_texture_entropy_high():
    """Test texture entropy for high-texture (noisy) images."""
    # Noisy image should have high entropy
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frames = [frame]
    entropy = calculate_texture_entropy(frames)
    assert entropy > 0.3, f"Noisy image should have high entropy, got {entropy}"

def test_sequence_classification():
    """Test sequence classification logic."""
    # Static, low texture
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    motion_class, texture_class = classify_sequence([frame, frame.copy()])
    assert motion_class == 'Static', f"Expected Static, got {motion_class}"
    assert texture_class == 'Low', f"Expected Low, got {texture_class}"

def test_stratification_metadata_structure():
    """Test that stratification produces correct metadata structure."""
    stratified_dir = get_stratified_dir()
    metadata_path = stratified_dir / "stratification_metadata.json"
    
    if not metadata_path.exists():
        # Skip if stratification hasn't been run yet
        return
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'total_sequences' in metadata
    assert 'strata_counts' in metadata
    assert 'selected_counts' in metadata
    assert 'seed' in metadata
    
    # Check strata keys
    expected_strata = ['Static-High', 'Static-Low', 'Fast-High', 'Fast-Low']
    for stratum in expected_strata:
        assert stratum in metadata['selected_counts'], f"Missing stratum: {stratum}"
        assert metadata['selected_counts'][stratum] >= MIN_SEQUENCE_PER_STRATUM, \
            f"Stratum {stratum} has fewer than {MIN_SEQUENCE_PER_STRATUM} sequences"

if __name__ == "__main__":
    # Run tests
    test_optical_flow_magnitude_static()
    test_optical_flow_magnitude_moving()
    test_texture_entropy_low()
    test_texture_entropy_high()
    test_sequence_classification()
    test_stratification_metadata_structure()
    print("All tests passed!")
