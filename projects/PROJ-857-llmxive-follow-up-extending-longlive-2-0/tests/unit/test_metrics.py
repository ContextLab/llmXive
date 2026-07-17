"""
Unit tests for evaluation/metrics.py

These tests verify that the temporal coherence and motion smoothness
calculations work correctly on CPU with various inputs.
"""
import pytest
import torch
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from evaluation.metrics import (
    calculate_temporal_coherence,
    calculate_motion_smoothness,
    aggregate_video_scores
)
from evaluation.clip_evaluator import create_clip_evaluator

class TestTemporalCoherence:
    def test_single_clip_tensor(self):
        """Test with a single clip as a torch tensor."""
        # Create a coherent clip (frames are similar)
        base_frame = torch.rand(1, 64, 64, 3) * 255.0
        clip = torch.cat([base_frame + torch.rand(64, 64, 3) * 5 for _ in range(5)], dim=0)
        
        score = calculate_temporal_coherence(clip, device="cpu")
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0, f"Score {score} out of range [0, 1]"
    
    def test_list_of_arrays(self):
        """Test with a list of numpy arrays."""
        base_frame = np.random.rand(64, 64, 3) * 255.0
        frames = [base_frame + np.random.rand(64, 64, 3) * 5 for _ in range(5)]
        
        score = calculate_temporal_coherence(frames, device="cpu")
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_insufficient_frames(self):
        """Test that a clip with < 2 frames raises an error."""
        single_frame = torch.rand(1, 64, 64, 3) * 255.0
        
        with pytest.raises(ValueError, match="at least 2 frames"):
            calculate_temporal_coherence(single_frame, device="cpu")
    
    def test_incoherent_clip(self):
        """Test with random noise (should yield lower coherence)."""
        random_clip = torch.rand(10, 64, 64, 3) * 255.0
        score = calculate_temporal_coherence(random_clip, device="cpu")
        
        # Just ensure it runs and returns a valid score
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

class TestMotionSmoothness:
    def test_smooth_motion(self):
        """Test with a clip showing smooth, constant motion."""
        # Create a moving object (simple translation)
        T, H, W, C = 10, 64, 64, 3
        clip = torch.zeros(T, H, W, C)
        for t in range(T):
            # Shift a block of pixels
            y_start = int(t * H / T)
            y_end = y_start + 10
            x_start = int(t * W / T)
            x_end = x_start + 10
            if y_end <= H and x_end <= W:
                clip[t, y_start:y_end, x_start:x_end, :] = 255.0
        
        score = calculate_motion_smoothness(clip, device="cpu")
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_erratic_motion(self):
        """Test with random noise (should yield lower smoothness)."""
        random_clip = torch.rand(10, 64, 64, 3) * 255.0
        score = calculate_motion_smoothness(random_clip, device="cpu")
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_single_frame(self):
        """Test with a single frame (should return 1.0)."""
        single_frame = torch.rand(1, 64, 64, 3) * 255.0
        score = calculate_motion_smoothness(single_frame, device="cpu")
        
        assert score == 1.0

class TestAggregateVideoScores:
    def test_aggregate_basic(self):
        """Test basic aggregation."""
        coherence = [0.8, 0.9, 0.85]
        smoothness = [0.7, 0.75, 0.65]
        
        result = aggregate_video_scores(coherence, smoothness)
        
        assert 'coherence' in result
        assert 'smoothness' in result
        assert 'composite' in result
        assert 'count' in result
        assert result['count'] == 3
        
        # Check means
        assert abs(result['coherence'] - 0.85) < 0.01
        assert abs(result['smoothness'] - 0.7) < 0.01
    
    def test_aggregate_no_smoothness(self):
        """Test aggregation without smoothness scores."""
        coherence = [0.8, 0.9]
        
        result = aggregate_video_scores(coherence)
        
        assert 'coherence' in result
        assert 'smoothness' not in result
        assert 'composite' in result
    
    def test_aggregate_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        coherence = [0.8, 0.9]
        smoothness = [0.7]
        
        with pytest.raises(ValueError, match="same length"):
            aggregate_video_scores(coherence, smoothness)
    
    def test_aggregate_empty(self):
        """Test that empty coherence list raises an error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            aggregate_video_scores([])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])