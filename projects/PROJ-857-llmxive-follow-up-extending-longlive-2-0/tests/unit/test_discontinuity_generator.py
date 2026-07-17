"""
Unit tests for discontinuity_generator.py
"""
import os
import sys
import tempfile
import json
import numpy as np
import torch
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.discontinuity_generator import _create_synthetic_clip, _seed_everything

class TestDiscontinuityGenerator:
    def test_seed_reproducibility(self):
        """Test that seeding produces deterministic results."""
        _seed_everything(42)
        val1 = random.random()
        
        _seed_everything(42)
        val2 = random.random()
        
        assert val1 == val2

    def test_no_discontinuity(self):
        """Test that 'none' type returns frames unchanged."""
        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(10)]
        original_frames = [f.copy() for f in frames]
        
        result, dtype = _create_synthetic_clip(frames, 'none')
        
        assert dtype == 'none'
        for r, o in zip(result, original_frames):
            np.testing.assert_array_equal(r, o)

    def test_frame_swap(self):
        """Test that 'frame_swap' swaps the middle two frames."""
        frames = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(6)]
        # Set unique values for middle frames
        frames[2][0, 0, 0] = 100
        frames[3][0, 0, 0] = 200
        
        result, dtype = _create_synthetic_clip(frames, 'frame_swap')
        
        assert dtype == 'frame_swap'
        assert result[2][0, 0, 0] == 200
        assert result[3][0, 0, 0] == 100

    def test_cut(self):
        """Test that 'cut' replaces middle frame with zeros."""
        frames = [np.ones((10, 10, 3), dtype=np.uint8) * 255 for _ in range(6)]
        
        result, dtype = _create_synthetic_clip(frames, 'cut')
        
        assert dtype == 'cut'
        mid = len(frames) // 2
        assert np.all(result[mid] == 0)
        assert np.all(result[0] == 255) # First frame unchanged

    def test_short_clip_handling(self):
        """Test that short clips (< 4 frames) are handled gracefully."""
        frames = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(2)]
        
        result, dtype = _create_synthetic_clip(frames, 'frame_swap')
        assert dtype == 'none' # Should fallback to none
        np.testing.assert_array_equal(result[0], frames[0])