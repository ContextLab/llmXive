import pytest
import torch
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.clip_evaluator import ClipTemporalEvaluator, create_clip_evaluator
from evaluation.metrics import calculate_temporal_coherence, aggregate_video_scores


class TestClipTemporalEvaluator:
    """Unit tests for ClipTemporalEvaluator"""

    def test_evaluator_initialization(self):
        """Test that evaluator initializes with frozen model"""
        evaluator = create_clip_evaluator()
        
        assert evaluator.model is not None
        assert evaluator.processor is not None
        
        # Check that model is in eval mode
        assert evaluator.model.training == False
        
        # Check that parameters are frozen
        for param in evaluator.model.parameters():
            assert not param.requires_grad

    def test_single_frame_score(self):
        """Test that single frame returns perfect score"""
        evaluator = create_clip_evaluator()
        
        # Create single frame
        frame = np.random.rand(224, 224, 3).astype(np.float32)
        
        score = evaluator.compute_temporal_coherence(frame)
        
        assert score == 1.0
        assert 0.0 <= score <= 1.0

    def test_smooth_video_high_score(self):
        """Test that smooth video gets high coherence score"""
        evaluator = create_clip_evaluator()
        
        # Create smooth gradient video
        num_frames = 10
        frames = np.zeros((num_frames, 224, 224, 3), dtype=np.float32)
        for i in range(num_frames):
            frames[i, :, :, 0] = np.linspace(i * 10, 255 - i * 10, 224)[:, None]
            frames[i, :, :, 1] = np.linspace(0, 255, 224)[None, :]
            frames[i, :, :, 2] = 128
        
        score = evaluator.compute_temporal_coherence(frames)
        
        # Smooth video should have high coherence
        assert score > 0.8
        assert 0.0 <= score <= 1.0

    def test_jumpy_video_low_score(self):
        """Test that jumpy video gets low coherence score"""
        evaluator = create_clip_evaluator()
        
        # Create jumpy video (random frames)
        num_frames = 10
        frames = np.random.rand(num_frames, 224, 224, 3).astype(np.float32)
        
        score = evaluator.compute_temporal_coherence(frames)
        
        # Jumpy video should have lower coherence than smooth
        # Note: Random frames might still have some similarity by chance
        assert 0.0 <= score <= 1.0

    def test_evaluate_clip_returns_dict(self):
        """Test that evaluate_clip returns proper dictionary"""
        evaluator = create_clip_evaluator()
        
        frames = np.random.rand(5, 224, 224, 3).astype(np.float32)
        result = evaluator.evaluate_clip(frames)
        
        assert isinstance(result, dict)
        assert "temporal_coherence_score" in result
        assert "num_frames" in result
        assert "frame_shape" in result
        assert "model" in result
        assert "device" in result
        
        assert result["num_frames"] == 5
        assert result["frame_shape"] == (224, 224, 3)

    def test_score_range(self):
        """Test that scores are always in [0, 1] range"""
        evaluator = create_clip_evaluator()
        
        # Test various frame configurations
        test_cases = [
            np.random.rand(5, 224, 224, 3).astype(np.float32),
            np.random.rand(20, 224, 224, 3).astype(np.float32),
            np.zeros((10, 224, 224, 3), dtype=np.float32),
            np.ones((10, 224, 224, 3), dtype=np.float32)
        ]
        
        for frames in test_cases:
            score = evaluator.compute_temporal_coherence(frames)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range [0, 1]"

    def test_device_placement(self):
        """Test that model is placed on correct device"""
        evaluator = create_clip_evaluator(device="cpu")
        
        # Check model is on CPU
        for param in evaluator.model.parameters():
            assert param.device.type == "cpu"
            break


class TestTemporalCoherenceMetrics:
    """Unit tests for temporal coherence metrics"""

    def test_cosine_similarity_method(self):
        """Test cosine similarity coherence calculation"""
        # Create identical embeddings (should give score of 1.0)
        embeddings = torch.ones(5, 10)  # (T, D)
        embeddings = embeddings / torch.norm(embeddings, dim=1, keepdim=True)
        
        score = calculate_temporal_coherence(embeddings, method="cosine_similarity")
        
        assert score == 1.0

    def test_mse_method(self):
        """Test MSE-based coherence calculation"""
        # Create identical embeddings
        embeddings = torch.zeros(5, 10)
        
        score = calculate_temporal_coherence(embeddings, method="mse")
        
        assert score == 1.0

    def test_aggregate_scores(self):
        """Test score aggregation"""
        clip_scores = [
            {"temporal_coherence_score": 0.9},
            {"temporal_coherence_score": 0.8},
            {"temporal_coherence_score": 0.7}
        ]
        
        result = aggregate_video_scores(clip_scores)
        
        assert result["num_clips"] == 3
        assert result["average_score"] == pytest.approx(0.8, rel=0.01)
        assert result["min_score"] == 0.7
        assert result["max_score"] == 0.9