"""
Unit tests for fallback logic in heuristics.

Tests for T018: Implement fallback logic in code/heuristics/ to select
first k blocks if all scores are near-zero.
"""
import pytest
import numpy as np
import sys
import os
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from heuristics.fallback import (
    FallbackConfig,
    is_scores_degenerate,
    select_fallback_blocks,
    apply_fallback_if_needed,
    FallbackHeuristicWrapper
)
from heuristics.base import HeuristicSelector


class TestDegenerateScoreDetection:
    """Tests for is_scores_degenerate function."""
    
    def test_all_zeros_are_degenerate(self):
        """All zero scores should be detected as degenerate."""
        scores = np.zeros(100)
        assert is_scores_degenerate(scores, 1e-6) is True
    
    def test_very_small_scores_are_degenerate(self):
        """Very small scores should be detected as degenerate."""
        scores = np.full(100, 1e-10)
        assert is_scores_degenerate(scores, 1e-6) is True
    
    def test_normal_scores_not_degenerate(self):
        """Normal scores should not be detected as degenerate."""
        scores = np.random.rand(100)
        assert is_scores_degenerate(scores, 1e-6) is False
    
    def test_mixed_scores_not_degenerate(self):
        """Mixed scores with some large values should not be degenerate."""
        scores = np.random.rand(100)
        scores[0] = 100.0  # One large value
        assert is_scores_degenerate(scores, 1e-6) is False
    
    def test_empty_scores_degenerate(self):
        """Empty scores should be detected as degenerate."""
        scores = np.array([])
        assert is_scores_degenerate(scores, 1e-6) is True
    
    def test_none_scores_degenerate(self):
        """None scores should be detected as degenerate."""
        assert is_scores_degenerate(None, 1e-6) is True
    
    def test_threshold_sensitivity(self):
        """Scores near threshold should be handled correctly."""
        scores = np.full(100, 1e-6)  # Exactly at threshold
        assert is_scores_degenerate(scores, 1e-6) is False  # Not strictly less
        
        scores = np.full(100, 0.9e-6)  # Just below threshold
        assert is_scores_degenerate(scores, 1e-6) is True


class TestFallbackBlockSelection:
    """Tests for select_fallback_blocks function."""
    
    def test_basic_selection(self):
        """Basic fallback selection should return first k blocks."""
        selected = select_fallback_blocks(100, 10)
        assert selected == list(range(10))
    
    def test_k_exceeds_num_blocks(self):
        """When k > num_blocks, should return all available blocks."""
        selected = select_fallback_blocks(5, 10)
        assert selected == list(range(5))
    
    def test_min_blocks_enforcement(self):
        """Min blocks should be enforced even if k is smaller."""
        selected = select_fallback_blocks(100, 5, min_blocks=10)
        assert selected == list(range(10))
    
    def test_max_blocks_enforcement(self):
        """Max blocks should be enforced even if k is larger."""
        selected = select_fallback_blocks(100, 50, max_blocks=20)
        assert selected == list(range(20))
    
    def test_combined_limits(self):
        """Min and max blocks should work together."""
        selected = select_fallback_blocks(100, 100, min_blocks=5, max_blocks=15)
        assert selected == list(range(15))
    
    def test_single_block(self):
        """Should handle single block case."""
        selected = select_fallback_blocks(1, 1)
        assert selected == [0]


class TestApplyFallbackIfNeeded:
    """Tests for apply_fallback_if_needed function."""
    
    def test_degenerate_scores_triggers_fallback(self):
        """Degenerate scores should trigger fallback selection."""
        scores = np.zeros(100)
        selected, was_fallback = apply_fallback_if_needed(
            scores, num_blocks=100,
            config=FallbackConfig(k_blocks=10, score_threshold=1e-6)
        )
        assert was_fallback is True
        assert selected == list(range(10))
    
    def test_normal_scores_no_fallback(self):
        """Normal scores should not trigger fallback."""
        scores = np.random.rand(100)
        selected, was_fallback = apply_fallback_if_needed(
            scores, num_blocks=100,
            config=FallbackConfig(k_blocks=10, score_threshold=1e-6)
        )
        assert was_fallback is False
        # Should be top-k by score
        assert len(selected) == 10
        assert all(0 <= idx < 100 for idx in selected)
    
    def test_custom_config_applied(self):
        """Custom config should be respected."""
        scores = np.zeros(100)
        selected, was_fallback = apply_fallback_if_needed(
            scores, num_blocks=100,
            config=FallbackConfig(k_blocks=25, score_threshold=1e-6)
        )
        assert was_fallback is True
        assert selected == list(range(25))


class TestFallbackHeuristicWrapper:
    """Tests for FallbackHeuristicWrapper class."""
    
    class MockHeuristic(HeuristicSelector):
        """Mock heuristic for testing."""
        
        def __init__(self, return_scores=None):
            self.return_scores = return_scores
        
        def compute_scores(self, attention_logits, **kwargs):
            if self.return_scores is not None:
                return self.return_scores
            return np.random.rand(len(attention_logits))
        
        def select_blocks(self, attention_logits, **kwargs):
            return []
    
    def test_wrapper_with_degenerate_scores(self):
        """Wrapper should use fallback when scores are degenerate."""
        mock = self.MockHeuristic(return_scores=np.zeros(50))
        wrapper = FallbackHeuristicWrapper(
            mock,
            FallbackConfig(k_blocks=5, score_threshold=1e-6)
        )
        
        dummy_logits = np.random.rand(50, 128)
        selected = wrapper.select_blocks(dummy_logits)
        
        assert selected == list(range(5))
        assert wrapper.get_stats()["fallback_count"] == 1
    
    def test_wrapper_with_normal_scores(self):
        """Wrapper should use normal selection when scores are valid."""
        mock = self.MockHeuristic(return_scores=np.random.rand(50))
        wrapper = FallbackHeuristicWrapper(
            mock,
            FallbackConfig(k_blocks=5, score_threshold=1e-6)
        )
        
        dummy_logits = np.random.rand(50, 128)
        selected = wrapper.select_blocks(dummy_logits)
        
        assert wrapper.get_stats()["fallback_count"] == 0
        assert len(selected) == 5
    
    def test_wrapper_stats_accuracy(self):
        """Wrapper stats should accurately track calls."""
        mock = self.MockHeuristic(return_scores=np.zeros(50))
        wrapper = FallbackHeuristicWrapper(
            mock,
            FallbackConfig(k_blocks=5, score_threshold=1e-6)
        )
        
        dummy_logits = np.random.rand(50, 128)
        
        # First call
        wrapper.select_blocks(dummy_logits)
        stats = wrapper.get_stats()
        assert stats["total_calls"] == 1
        assert stats["fallback_count"] == 1
        assert stats["fallback_rate"] == 1.0
        
        # Second call
        wrapper.select_blocks(dummy_logits)
        stats = wrapper.get_stats()
        assert stats["total_calls"] == 2
        assert stats["fallback_count"] == 2
        assert stats["fallback_rate"] == 1.0
    
    def test_wrapper_with_mixed_scores(self):
        """Wrapper should handle alternating degenerate/normal scores."""
        call_count = [0]
        
        class FlakyHeuristic(HeuristicSelector):
            def compute_scores(self, attention_logits, **kwargs):
                call_count[0] += 1
                if call_count[0] % 2 == 0:
                    return np.random.rand(len(attention_logits))
                return np.zeros(len(attention_logits))
            
            def select_blocks(self, attention_logits, **kwargs):
                return []
        
        mock = FlakyHeuristic()
        wrapper = FallbackHeuristicWrapper(
            mock,
            FallbackConfig(k_blocks=5, score_threshold=1e-6)
        )
        
        dummy_logits = np.random.rand(50, 128)
        
        # First call: degenerate
        wrapper.select_blocks(dummy_logits)
        assert wrapper.get_stats()["fallback_count"] == 1
        
        # Second call: normal
        wrapper.select_blocks(dummy_logits)
        assert wrapper.get_stats()["fallback_count"] == 1  # No change
        
        # Third call: degenerate
        wrapper.select_blocks(dummy_logits)
        assert wrapper.get_stats()["fallback_count"] == 2


class TestFallbackConfig:
    """Tests for FallbackConfig dataclass."""
    
    def test_default_values(self):
        """Default config values should be sensible."""
        config = FallbackConfig()
        assert config.k_blocks == 10
        assert config.score_threshold == 1e-6
        assert config.min_blocks == 1
        assert config.max_blocks == 100
    
    def test_custom_values(self):
        """Custom config values should be applied."""
        config = FallbackConfig(
            k_blocks=20,
            score_threshold=1e-4,
            min_blocks=5,
            max_blocks=50
        )
        assert config.k_blocks == 20
        assert config.score_threshold == 1e-4
        assert config.min_blocks == 5
        assert config.max_blocks == 50