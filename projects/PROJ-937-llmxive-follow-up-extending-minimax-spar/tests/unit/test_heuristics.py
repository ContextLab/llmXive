import pytest
import numpy as np
import sys
import os

# Ensure code/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from heuristics.base import HeuristicSelector
from heuristics.entropy import BlockEntropyHeuristic, HeuristicConfig as EntropyConfig
from heuristics.gradient import GradientMagnitudeHeuristic, HeuristicConfig as GradientConfig
from heuristics.recency import RecencyBiasHeuristic, HeuristicConfig as RecencyConfig
from heuristics.fallback import FallbackHeuristicWrapper, FallbackConfig


class TestEntropy:
    def test_entropy_returns_float(self):
        """Test that entropy heuristic returns a float score."""
        config = EntropyConfig()
        heuristic = BlockEntropyHeuristic(config)
        # Mock attention logits
        logits = np.random.randn(4, 64, 128)  # (batch, heads, seq_len)
        scores = heuristic.compute_scores(logits)
        assert isinstance(scores, np.ndarray)
        assert len(scores) > 0
        assert all(isinstance(s, (float, np.floating)) for s in scores)

    def test_entropy_block_returns_expected(self):
        """Test entropy calculation with known input."""
        config = EntropyConfig()
        heuristic = BlockEntropyHeuristic(config)
        # Create logits with known entropy properties
        # High entropy: uniform distribution
        # Low entropy: concentrated distribution
        logits_high_entropy = np.ones((1, 1, 128)) * 0.1  # Uniform-ish
        logits_low_entropy = np.zeros((1, 1, 128))
        logits_low_entropy[0, 0, 0] = 10.0  # Concentrated at index 0
        
        scores_high = heuristic.compute_scores(logits_high_entropy)
        scores_low = heuristic.compute_scores(logits_low_entropy)
        
        # High entropy should result in higher block scores (more uncertainty)
        # Low entropy should result in lower block scores
        assert scores_high.mean() > scores_low.mean(), \
            "High entropy input should yield higher scores than low entropy input"


class TestGradient:
    def test_gradient_norms_match_proxy_loss(self):
        """Test that gradient norms correlate with proxy loss."""
        config = GradientConfig()
        heuristic = GradientMagnitudeHeuristic(config)
        
        # Simulate different gradient magnitudes
        # Higher gradients should indicate more informative blocks
        grad_low = np.random.randn(10) * 0.01
        grad_high = np.random.randn(10) * 10.0
        
        scores_low = heuristic.compute_scores(grad_low)
        scores_high = heuristic.compute_scores(grad_high)
        
        assert scores_high.mean() > scores_low.mean(), \
            "Higher gradient magnitudes should yield higher scores"

    def test_gradient_norms_match_proxy_loss(self):
        """Test that gradient norms correlate with proxy loss."""
        config = GradientConfig()
        heuristic = GradientMagnitudeHeuristic(config)
        
        # Simulate different gradient magnitudes
        # Higher gradients should indicate more informative blocks
        grad_low = np.random.randn(10) * 0.01
        grad_high = np.random.randn(10) * 10.0
        
        scores_low = heuristic.compute_scores(grad_low)
        scores_high = heuristic.compute_scores(grad_high)
        
        assert scores_high.mean() > scores_low.mean(), \
            "Higher gradient magnitudes should yield higher scores"


class TestRecency:
    def test_recency_returns_float(self):
        """Test that recency heuristic returns a float score."""
        config = RecencyConfig()
        heuristic = RecencyBiasHeuristic(config)
        # Mock positions (recent positions have higher indices)
        positions = np.arange(128)
        scores = heuristic.compute_scores(positions)
        assert isinstance(scores, np.ndarray)
        assert len(scores) > 0
        assert all(isinstance(s, (float, np.floating)) for s in scores)

    def test_recency_bias_weights_sum_to_one(self):
        """Test that recency bias weights sum to one after normalization."""
        config = RecencyConfig()
        heuristic = RecencyBiasHeuristic(config)
        
        # Test with various position arrays
        positions = np.arange(64)
        scores = heuristic.compute_scores(positions)
        
        # The heuristic should normalize weights to sum to 1
        # (depending on implementation, this might be internal)
        # We verify that the output is a valid probability distribution
        assert np.isclose(scores.sum(), 1.0, atol=1e-5) or \
               np.isclose(scores.max(), 1.0, atol=1e-5), \
               "Recency scores should be normalized or peak at 1.0"


class TestFallback:
    def test_fallback_selects_first_k_when_scores_zero(self):
        """Test that fallback selects first k blocks when all scores are near-zero."""
        config = FallbackConfig(
            near_zero_threshold=1e-6,
            default_top_k=4
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        # Create scores that are all near-zero
        num_blocks = 10
        near_zero_scores = np.array([1e-7, 1e-8, 1e-9, 1e-10, 1e-11, 
                                     1e-12, 1e-13, 1e-14, 1e-15, 1e-16])
        
        selected = wrapper.select_blocks(near_zero_scores, num_blocks=num_blocks, top_k=4)
        
        # Should select first 4 blocks: [0, 1, 2, 3]
        expected = [0, 1, 2, 3]
        assert selected == expected, \
            f"Expected first 4 blocks {expected}, got {selected}"

    def test_fallback_selects_first_k_when_scores_all_zeros(self):
        """Test fallback with all-zero scores."""
        config = FallbackConfig(
            near_zero_threshold=1e-6,
            default_top_k=3
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        num_blocks = 8
        zero_scores = np.zeros(num_blocks)
        
        selected = wrapper.select_blocks(zero_scores, num_blocks=num_blocks, top_k=3)
        
        expected = [0, 1, 2]
        assert selected == expected, \
            f"Expected first 3 blocks {expected}, got {selected}"

    def test_fallback_selects_first_k_when_scores_below_threshold(self):
        """Test fallback with scores just below threshold."""
        config = FallbackConfig(
            near_zero_threshold=1e-5,
            default_top_k=5
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        num_blocks = 10
        # All scores below 1e-5
        low_scores = np.array([1e-6, 2e-6, 3e-6, 4e-6, 5e-6, 
                               6e-6, 7e-6, 8e-6, 9e-6, 1e-6])
        
        selected = wrapper.select_blocks(low_scores, num_blocks=num_blocks, top_k=5)
        
        expected = [0, 1, 2, 3, 4]
        assert selected == expected, \
            f"Expected first 5 blocks {expected}, got {selected}"

    def test_fallback_uses_normal_logic_when_scores_above_threshold(self):
        """Test that normal selection logic is used when scores are above threshold."""
        config = FallbackConfig(
            near_zero_threshold=1e-6,
            default_top_k=3
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        num_blocks = 10
        # Mix of scores, some above threshold
        mixed_scores = np.array([0.0, 0.1, 0.5, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        selected = wrapper.select_blocks(mixed_scores, num_blocks=num_blocks, top_k=3)
        
        # Should select top 3: indices 4 (0.8), 2 (0.5), 1 (0.1)
        expected = [4, 2, 1]
        assert selected == expected, \
            f"Expected top 3 blocks {expected}, got {selected}"

    def test_fallback_handles_empty_scores(self):
        """Test fallback with empty scores array."""
        config = FallbackConfig(
            near_zero_threshold=1e-6,
            default_top_k=3
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        selected = wrapper.select_blocks(np.array([]), num_blocks=0, top_k=3)
        
        assert selected == [], f"Expected empty list, got {selected}"

    def test_fallback_respects_top_k_limit(self):
        """Test that fallback respects top_k limit even when more blocks available."""
        config = FallbackConfig(
            near_zero_threshold=1e-6,
            default_top_k=100  # High default
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        num_blocks = 5
        near_zero_scores = np.zeros(num_blocks)
        
        # Request top_k=2, should get only 2 blocks
        selected = wrapper.select_blocks(near_zero_scores, num_blocks=num_blocks, top_k=2)
        
        expected = [0, 1]
        assert selected == expected, \
            f"Expected first 2 blocks {expected}, got {selected}"

    def test_fallback_configurable_threshold(self):
        """Test that the near-zero threshold is configurable."""
        config = FallbackConfig(
            near_zero_threshold=1e-3,  # Higher threshold
            default_top_k=2
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        num_blocks = 5
        # Scores between 1e-4 and 1e-3 (below 1e-3 threshold)
        scores = np.array([1e-4, 2e-4, 5e-4, 8e-4, 9e-4])
        
        selected = wrapper.select_blocks(scores, num_blocks=num_blocks, top_k=2)
        
        # Should trigger fallback
        expected = [0, 1]
        assert selected == expected, \
            f"Expected fallback to first 2 blocks {expected}, got {selected}"

    def test_fallback_configurable_threshold_not_triggered(self):
        """Test that fallback is not triggered when scores are above custom threshold."""
        config = FallbackConfig(
            near_zero_threshold=1e-3,  # Higher threshold
            default_top_k=2
        )
        wrapper = FallbackHeuristicWrapper(config)
        
        num_blocks = 5
        # Scores above 1e-3
        scores = np.array([0.01, 0.02, 0.05, 0.1, 0.2])
        
        selected = wrapper.select_blocks(scores, num_blocks=num_blocks, top_k=2)
        
        # Should select top 2: indices 4 (0.2), 3 (0.1)
        expected = [4, 3]
        assert selected == expected, \
            f"Expected top 2 blocks {expected}, got {selected}"
