"""
Contract tests for the CLIP Evaluator.

Verifies that the output format and basic behavior of the evaluator
match the expected contract (numeric score, no gradients).
"""
import pytest
import torch
import numpy as np
from evaluation.clip_evaluator import create_clip_evaluator, ClipTemporalEvaluator

class TestClipEvaluatorContract:
    """Contract tests for ClipTemporalEvaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create a lightweight evaluator instance for testing."""
        # Use a smaller model or default if available; for testing we assume
        # the model can be loaded. In CI, this might be cached.
        return create_clip_evaluator(model_name="openai/clip-vit-base-patch32")

    def test_model_is_frozen(self, evaluator):
        """Verify that the loaded model has no trainable parameters."""
        for param in evaluator.model.parameters():
            assert not param.requires_grad, "Model parameters must be frozen."

    def test_model_is_eval_mode(self, evaluator):
        """Verify that the model is in evaluation mode."""
        assert evaluator.model.training is False, "Model must be in eval mode."

    def test_single_clip_score_is_float(self, evaluator):
        """Verify that scoring a single clip returns a float."""
        # Create a dummy clip: 10 frames, 224x224, 3 channels
        dummy_clip = np.random.randint(0, 255, (10, 224, 224, 3), dtype=np.uint8)
        score = evaluator.compute_temporal_coherence(dummy_clip)
        
        assert isinstance(score, float), f"Score must be a float, got {type(score)}"
        assert np.isfinite(score), "Score must be finite (no NaN/Inf)."

    def test_score_range(self, evaluator):
        """Verify that the score is within the theoretical range of cosine similarity [-1, 1]."""
        dummy_clip = np.random.randint(0, 255, (10, 224, 224, 3), dtype=np.uint8)
        score = evaluator.compute_temporal_coherence(dummy_clip)
        
        assert -1.0 <= score <= 1.0, f"Score {score} out of range [-1, 1]."

    def test_batch_score_returns_list(self, evaluator):
        """Verify that scoring a batch returns a list of floats."""
        clips = [
            np.random.randint(0, 255, (5, 224, 224, 3), dtype=np.uint8)
            for _ in range(3)
        ]
        scores = evaluator.score_batch(clips)
        
        assert isinstance(scores, list), "Batch scores must be a list."
        assert len(scores) == 3, "Number of scores must match number of clips."
        for s in scores:
            assert isinstance(s, float), "Each score must be a float."
            assert np.isfinite(s), "Each score must be finite."

    def test_no_gradient_flow(self, evaluator):
        """Verify that no gradients are computed during inference."""
        dummy_clip = np.random.randint(0, 255, (5, 224, 224, 3), dtype=np.uint8)
        
        # Wrap in tensor and require grad just to see if it propagates (it shouldn't)
        # But the evaluator uses torch.no_grad() internally, so we just check
        # that the model doesn't accumulate grads after a forward pass.
        with torch.no_grad():
            score = evaluator.compute_temporal_coherence(dummy_clip)
        
        # Check that no gradients were accumulated (model is frozen + no_grad)
        for param in evaluator.model.parameters():
            assert param.grad is None, "No gradients should be accumulated."