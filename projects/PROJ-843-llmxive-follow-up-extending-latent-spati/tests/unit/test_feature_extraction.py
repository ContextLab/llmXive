"""
Unit tests for code/data/extract_features.py
Tests cover:
- SIFT/ORB descriptor extraction
- Fast sequence detection logic
- Coordinate validity
"""
import os
import sys
import json
import cv2
import numpy as np
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.extract_features import (
    load_sequence_frames,
    extract_sparse_features,
    is_fast_sequence,
    process_sequence
)
from utils.seeds import set_global_seed
from config import get_stratified_dir, get_features_dir

@pytest.fixture(autouse=True)
def setup_seed():
    set_global_seed(42)

class TestLoadSequenceFrames:
    def test_load_valid_sequence(self, tmp_path):
        """Test loading frames from a valid sequence directory."""
        seq_dir = tmp_path / "test_seq"
        seq_dir.mkdir()
        
        # Create dummy frames
        for i in range(5):
            img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            cv2.imwrite(str(seq_dir / f"frame_{i:04d}.png"), img)
        
        frames = load_sequence_frames(str(seq_dir))
        
        assert len(frames) == 5
        assert all(isinstance(f, np.ndarray) for f in frames)
        assert frames[0].shape == (100, 100, 3)

    def test_load_empty_sequence(self, tmp_path):
        """Test loading from an empty directory raises appropriate error."""
        seq_dir = tmp_path / "empty_seq"
        seq_dir.mkdir()
        
        with pytest.raises((FileNotFoundError, ValueError)):
            load_sequence_frames(str(seq_dir))

class TestExtractSparseFeatures:
    def test_extract_sift_features(self, tmp_path):
        """Test SIFT feature extraction on a valid frame."""
        img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        keypoints, descriptors = extract_sparse_features(gray, method="sift")
        
        assert isinstance(keypoints, list)
        assert isinstance(descriptors, np.ndarray) or descriptors is None
        
        # SIFT should find some keypoints on random noise
        assert len(keypoints) > 0

    def test_extract_orb_features(self, tmp_path):
        """Test ORB feature extraction on a valid frame."""
        img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        keypoints, descriptors = extract_sparse_features(gray, method="orb")
        
        assert isinstance(keypoints, list)
        assert isinstance(descriptors, np.ndarray) or descriptors is None
        assert len(keypoints) > 0

    def test_invalid_method(self, tmp_path):
        """Test that invalid method raises error."""
        img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        with pytest.raises(ValueError):
            extract_sparse_features(gray, method="invalid_method")

class TestIsFastSequence:
    def test_detect_fast_sequence(self, tmp_path):
        """Test detection of a fast-moving sequence."""
        seq_dir = tmp_path / "fast_seq"
        seq_dir.mkdir()
        
        # Create frames with significant motion
        for i in range(5):
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            # Move a white square across frames
            x = i * 20
            img[40:60, x:x+20] = 255
            cv2.imwrite(str(seq_dir / f"frame_{i:04d}.png"), img)
        
        frames = load_sequence_frames(str(seq_dir))
        # Convert to grayscale for optical flow
        gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        
        # Calculate optical flow magnitude manually
        flow_magnitudes = []
        for i in range(len(gray_frames) - 1):
            flow = cv2.calcOpticalFlowFarneback(
                gray_frames[i], gray_frames[i+1], None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            magnitude = cv2.magnitude(flow[:,:,0], flow[:,:,1])
            flow_magnitudes.append(np.mean(magnitude))
        
        avg_magnitude = np.mean(flow_magnitudes)
        
        # This sequence should be detected as fast
        assert is_fast_sequence(avg_magnitude)

    def test_detect_static_sequence(self, tmp_path):
        """Test detection of a static sequence."""
        seq_dir = tmp_path / "static_seq"
        seq_dir.mkdir()
        
        # Create identical frames
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        for i in range(5):
            cv2.imwrite(str(seq_dir / f"frame_{i:04d}.png"), img)
        
        frames = load_sequence_frames(str(seq_dir))
        gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        
        flow_magnitudes = []
        for i in range(len(gray_frames) - 1):
            flow = cv2.calcOpticalFlowFarneback(
                gray_frames[i], gray_frames[i+1], None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            magnitude = cv2.magnitude(flow[:,:,0], flow[:,:,1])
            flow_magnitudes.append(np.mean(magnitude))
        
        avg_magnitude = np.mean(flow_magnitudes)
        
        # This sequence should NOT be detected as fast
        assert not is_fast_sequence(avg_magnitude)

class TestProcessSequence:
    def test_process_sequence_integration(self, tmp_path):
        """Test the full sequence processing pipeline."""
        # Setup
        set_global_seed(42)
        seq_dir = tmp_path / "test_seq"
        seq_dir.mkdir()
        
        # Create test frames
        for i in range(5):
            img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
            cv2.imwrite(str(seq_dir / f"frame_{i:04d}.png"), img)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Process
        result = process_sequence(
            str(seq_dir),
            str(output_dir),
            method="sift",
            frame_step=1
        )
        
        # Verify output
        assert result is not None
        assert "num_frames" in result
        assert "num_keypoints" in result
        assert "output_file" in result
        
        # Check file was created
        assert os.path.exists(result["output_file"])

    def test_process_fast_sequence_marking(self, tmp_path):
        """Test that fast sequences are properly marked."""
        seq_dir = tmp_path / "fast_seq"
        seq_dir.mkdir()
        
        # Create frames with high motion
        for i in range(5):
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            x = i * 25
            img[40:60, x:x+20] = 255
            cv2.imwrite(str(seq_dir / f"frame_{i:04d}.png"), img)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = process_sequence(
            str(seq_dir),
            str(output_dir),
            method="sift",
            frame_step=1
        )
        
        # Fast sequences should be marked as invalid
        assert result.get("is_fast_sequence", False) is True
