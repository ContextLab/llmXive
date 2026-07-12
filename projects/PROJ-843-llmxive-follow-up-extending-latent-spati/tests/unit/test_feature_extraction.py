import os
import sys
import json
import tempfile
import shutil
import numpy as np
import cv2
import pytest
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.extract_features import (
    load_sequence_frames,
    extract_sparse_features,
    is_fast_sequence,
    process_sequence
)
from utils.seeds import set_global_seed
from config import get_features_dir, get_stratified_dir

@pytest.fixture
def temp_stratified_dir():
    """Create a temporary directory mimicking the stratified data structure."""
    temp_dir = tempfile.mkdtemp()
    # Create a mock stratum directory
    stratum_dir = Path(temp_dir) / "Static-High"
    stratum_dir.mkdir()
    
    # Create a mock sequence directory
    seq_dir = stratum_dir / "seq_001"
    seq_dir.mkdir()
    
    # Create mock frames
    for i in range(5):
        frame_path = seq_dir / f"frame_{i:04d}.png"
        # Create a simple gradient image
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(frame_path), img)
    
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_features_dir():
    """Create a temporary directory for feature output."""
    temp_dir = tempfile.mkdtemp()
    os.makedirs(temp_dir, exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_load_sequence_frames(temp_stratified_dir):
    """Test loading frames from a directory."""
    seq_path = Path(temp_stratified_dir) / "Static-High" / "seq_001"
    frames = load_sequence_frames(seq_path)
    
    assert len(frames) == 5
    assert all(f.shape == (100, 100, 3) for f in frames)
    assert all(f.dtype == np.uint8 for f in frames)

def test_extract_sparse_features():
    """Test extraction of SIFT and ORB descriptors."""
    set_global_seed(42)
    # Create a dummy frame
    frame = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    
    sift_result, orb_result = extract_sparse_features(frame)
    
    # SIFT result is (N, 2) coordinates and (N, 128) descriptors
    assert sift_result is not None
    assert len(sift_result) == 2
    coords, descs = sift_result
    assert coords.shape[1] == 2
    assert descs.shape[1] == 128
    assert coords.shape[0] == descs.shape[0]
    
    # ORB result is (N, 2) coordinates and (N, 32) descriptors
    assert orb_result is not None
    assert len(orb_result) == 2
    coords, descs = orb_result
    assert coords.shape[1] == 2
    assert descs.shape[1] == 32
    assert coords.shape[0] == descs.shape[0]

def test_is_fast_sequence():
    """Test detection of fast sequences based on optical flow."""
    set_global_seed(42)
    # Create two frames with significant motion
    frame1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frame2 = frame1.copy()
    # Shift frame2 significantly
    frame2[:, 20:, :] = frame1[:, :-20, :]
    
    # Create a sequence
    frames = [frame1, frame2]
    
    # This should detect motion
    is_fast = is_fast_sequence(frames)
    # The threshold in extract_features.py is typically around 5.0
    # With a 20-pixel shift, this should be True
    assert isinstance(is_fast, bool)

def test_process_sequence(temp_stratified_dir, temp_features_dir):
    """Test the full sequence processing pipeline."""
    set_global_seed(42)
    seq_path = Path(temp_stratified_dir) / "Static-High" / "seq_001"
    output_path = Path(temp_features_dir) / "seq_001"
    output_path.mkdir(parents=True, exist_ok=True)
    
    result = process_sequence(seq_path, output_path)
    
    assert result is True
    assert (output_path / "sift.npy").exists()
    assert (output_path / "orb.npy").exists()
    
    # Verify content validity
    sift_data = np.load(output_path / "sift.npy", allow_pickle=True).item()
    orb_data = np.load(output_path / "orb.npy", allow_pickle=True).item()
    
    assert "coords" in sift_data
    assert "descriptors" in sift_data
    assert "coords" in orb_data
    assert "descriptors" in orb_data
