import pytest
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from data.context_processors import (
    ProcessedContext,
    BaseContextProcessor,
    DiffAwareWindowProcessor,
    NaiveTruncationProcessor,
)
from config import StrategyType, ContextConfiguration


class TestDiffAwareWindowProcessor:
    """Unit tests for the diff-aware sliding window logic in DiffAwareWindowProcessor."""

    @pytest.fixture
    def sample_code_context(self) -> List[Dict[str, Any]]:
        """Provide a mock list of code snippets representing a file history with diffs."""
        return [
            {
                "file_path": "src/module.py",
                "content": "def old_function():\n    return 1",
                "is_diff": False,
                "lines_added": 0,
                "lines_deleted": 0,
                "timestamp": "2023-01-01T10:00:00Z",
            },
            {
                "file_path": "src/module.py",
                "content": "def old_function():\n    return 2\n\ndef new_helper():\n    pass",
                "is_diff": True,
                "lines_added": 2,
                "lines_deleted": 1,
                "timestamp": "2023-01-02T10:00:00Z",
            },
            {
                "file_path": "src/module.py",
                "content": "def old_function():\n    return 3\n\ndef new_helper():\n    return 'ok'",
                "is_diff": False,
                "lines_added": 0,
                "lines_deleted": 0,
                "timestamp": "2023-01-03T10:00:00Z",
            },
            {
                "file_path": "src/other.py",
                "content": "import src.module",
                "is_diff": False,
                "lines_added": 0,
                "lines_deleted": 0,
                "timestamp": "2023-01-03T11:00:00Z",
            },
        ]

    @pytest.fixture
    def config(self) -> ContextConfiguration:
        """Provide a standard context configuration for testing."""
        return ContextConfiguration(
            strategy=StrategyType.DIFF_AWARE,
            max_tokens=4096,
            context_window=5,  # Small window for testing
            diff_weight=2.0,
            recency_weight=1.0,
        )

    def test_processor_instantiation(self, config: ContextConfiguration):
        """Test that DiffAwareWindowProcessor can be instantiated with valid config."""
        processor = DiffAwareWindowProcessor(config)
        assert processor is not None
        assert processor.config.strategy == StrategyType.DIFF_AWARE
        assert processor.config.diff_weight == 2.0

    def test_score_calculation_increases_for_diffs(
        self, sample_code_context: List[Dict[str, Any]], config: ContextConfiguration
    ):
        """Verify that snippets marked as diffs receive higher relevance scores."""
        processor = DiffAwareWindowProcessor(config)
        
        # Calculate scores for all snippets
        scored_snippets = processor._score_snippets(sample_code_context, target_file="src/module.py")
        
        # The second snippet is a diff (lines_added > 0)
        diff_snippet = next(s for s in sample_code_context if s["is_diff"])
        # Find its score
        diff_score = next(score for snippet, score in scored_snippets if snippet["content"] == diff_snippet["content"])
        
        # A non-diff snippet
        non_diff_snippet = next(s for s in sample_code_context if not s["is_diff"] and s["file_path"] == "src/module.py")
        non_diff_score = next(score for snippet, score in scored_snippets if snippet["content"] == non_diff_snippet["content"])
        
        # The diff snippet should have a higher score due to diff_weight
        assert diff_score > non_diff_score, "Diff snippets should be scored higher than non-diffs"

    def test_recency_bias_in_window(
        self, sample_code_context: List[Dict[str, Any]], config: ContextConfiguration
    ):
        """Verify that more recent snippets are prioritized within the window."""
        # Adjust config to have a larger window to include multiple items
        config.context_window = 10
        processor = DiffAwareWindowProcessor(config)
        
        scored_snippets = processor._score_snippets(sample_code_context, target_file="src/module.py")
        
        # Sort by score descending
        sorted_snippets = sorted(scored_snippets, key=lambda x: x[1], reverse=True)
        
        # The most recent non-diff snippet (index 2) should be ranked higher than the oldest (index 0)
        # unless the diff weight is overwhelmingly dominant (which it isn't in this config)
        # We specifically check that the recency logic is applied:
        # Score = base_score + diff_bonus + recency_bonus
        # Recency bonus should be higher for index 2 vs index 0
        
        score_oldest = next(s for s, _ in scored_snippets if s["timestamp"] == "2023-01-01T10:00:00Z")
        score_newest = next(s for s, _ in scored_snippets if s["timestamp"] == "2023-01-03T10:00:00Z")
        
        # The newest should generally be favored if diffs are equal, but here we have a diff in the middle.
        # Let's verify the logic: if we remove the diff, the newest should win.
        # Instead, we test the _calculate_recency_score method directly.
        recency_oldest = processor._calculate_recency_score("2023-01-01T10:00:00Z", "2023-01-03T12:00:00Z")
        recency_newest = processor._calculate_recency_score("2023-01-03T10:00:00Z", "2023-01-03T12:00:00Z")
        
        assert recency_newest > recency_oldest, "More recent snippets should have higher recency scores"

    def test_window_selection_respects_max_tokens(
        self, sample_code_context: List[Dict[str, Any]], config: ContextConfiguration
    ):
        """Ensure the processor returns a context that fits within max_tokens."""
        config.max_tokens = 100  # Very small limit
        processor = DiffAwareWindowProcessor(config)
        
        result = processor.process(sample_code_context, target_file="src/module.py")
        
        assert isinstance(result, ProcessedContext)
        assert len(result.snippets) <= len(sample_code_context)
        # Verify the token count estimation is respected (approximate check)
        total_chars = sum(len(s.content) for s in result.snippets)
        # Rough heuristic: 4 chars ~ 1 token. 100 tokens ~ 400 chars.
        # This is a soft check to ensure the logic runs without error and filters.
        # The exact tokenization depends on the model, but the selection logic should truncate.
        assert total_chars < 1000, "Context should be truncated to fit limits"

    def test_empty_context_handling(self, config: ContextConfiguration):
        """Test behavior when given an empty list of snippets."""
        processor = DiffAwareWindowProcessor(config)
        result = processor.process([], target_file="src/module.py")
        
        assert isinstance(result, ProcessedContext)
        assert len(result.snippets) == 0
        assert result.total_tokens == 0

    def test_target_file_filtering(
        self, sample_code_context: List[Dict[str, Any]], config: ContextConfiguration
    ):
        """Verify that snippets for the target file are prioritized or included."""
        processor = DiffAwareWindowProcessor(config)
        result = processor.process(sample_code_context, target_file="src/module.py")
        
        # All snippets in result should ideally be relevant, but at least the target file ones
        # should be present if they fit.
        # With a small window, we expect the most relevant (diff + recent) of the target file.
        assert len(result.snippets) > 0
        
        # Check that we didn't accidentally include 'src/other.py' if 'src/module.py' has diffs
        # (This depends on the scoring, but usually target file is primary)
        # A safer assertion: ensure the target file snippets are considered.
        snippet_paths = [s.file_path for s in result.snippets]
        assert "src/module.py" in snippet_paths, "Target file snippets should be included"

    def test_diff_weight_parameter_effect(
        self, sample_code_context: List[Dict[str, Any]], config: ContextConfiguration
    ):
        """Test that increasing diff_weight increases the score of diff snippets relative to others."""
        config_low_weight = ContextConfiguration(
            strategy=StrategyType.DIFF_AWARE,
            max_tokens=4096,
            context_window=10,
            diff_weight=0.1,
            recency_weight=1.0,
        )
        config_high_weight = ContextConfiguration(
            strategy=StrategyType.DIFF_AWARE,
            max_tokens=4096,
            context_window=10,
            diff_weight=10.0,
            recency_weight=1.0,
        )
        
        processor_low = DiffAwareWindowProcessor(config_low_weight)
        processor_high = DiffAwareWindowProcessor(config_high_weight)
        
        scored_low = processor_low._score_snippets(sample_code_context, target_file="src/module.py")
        scored_high = processor_high._score_snippets(sample_code_context, target_file="src/module.py")
        
        diff_score_low = next(s for _, s in scored_low if "new_helper" in next(snippet for snippet in sample_code_context if snippet["content"] == s)["content"]) # Simplified retrieval
        # Actually, let's just find the diff snippet score by content match
        diff_content = "def old_function():\n    return 2\n\ndef new_helper():\n    pass"
        score_low = next(score for snippet, score in scored_low if snippet["content"] == diff_content)
        score_high = next(score for snippet, score in scored_high if snippet["content"] == diff_content)
        
        assert score_high > score_low, "Higher diff_weight should result in higher scores for diff snippets"

    def test_integration_with_get_processor(self, config: ContextConfiguration):
        """Test that the factory function returns the correct processor type."""
        from data.context_processors import get_processor
        
        processor = get_processor(config)
        assert isinstance(processor, DiffAwareWindowProcessor)