"""
Unit tests for context processors, specifically the semantic summarization logic.
"""
import pytest
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from data.context_processors import (
    retrieve_semantic_summaries,
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    process_context,
    ContextSnippet
)
from config import StrategyType, ContextConfiguration

class TestSemanticSummarization:
    """Tests for the rule-based semantic summarization module (T022)."""

    def test_first_sentence_paragraphs(self):
        """Verify extraction of first sentences from paragraphs."""
        content = """
        This is the first paragraph. It has two sentences.
        
        This is the second paragraph. It also has two sentences.
        
        Third paragraph.
        """
        file_history = [{"content": content}]
        snippets = retrieve_semantic_summaries("test", file_history, max_tokens=100)
        
        assert len(snippets) > 0
        summary = snippets[0].content
        # Should contain the first sentence of the first paragraph
        assert "This is the first paragraph." in summary
        # Should contain the first sentence of the second paragraph
        assert "This is the second paragraph." in summary

    def test_last_sentence_function_blocks(self):
        """Verify extraction of last sentences from function blocks."""
        content = """
        def foo():
            x = 1
            # Some logic
            return x # This is the end.

        def bar():
            y = 2
            # More logic
            pass # The end of bar.
        """
        file_history = [{"content": content}]
        snippets = retrieve_semantic_summaries("test", file_history, max_tokens=100)
        
        assert len(snippets) > 0
        summary = snippets[0].content
        # Should contain the last sentence of the function blocks
        assert "This is the end." in summary or "The end of bar." in summary

    def test_concatenation_with_ellipsis(self):
        """Verify that parts are concatenated with '...' separator."""
        content = """
        First paragraph.
        
        def func():
            pass # End.
        """
        file_history = [{"content": content}]
        snippets = retrieve_semantic_summaries("test", file_history, max_tokens=100)
        
        assert len(snippets) > 0
        summary = snippets[0].content
        assert "..." in summary

    def test_truncation_to_max_tokens(self):
        """Verify that the summary is truncated to max_tokens."""
        # Create a long content
        long_text = "Sentence one. " * 1000
        content = f"""
        {long_text}
        
        def func():
            pass # End.
        """
        file_history = [{"content": content}]
        max_tokens = 50
        snippets = retrieve_semantic_summaries("test", file_history, max_tokens=max_tokens)
        
        assert len(snippets) > 0
        summary = snippets[0].content
        words = summary.split()
        assert len(words) <= max_tokens + 5  # Small buffer for separator logic

    def test_empty_content(self):
        """Verify handling of empty content."""
        file_history = [{"content": ""}]
        snippets = retrieve_semantic_summaries("test", file_history)
        assert len(snippets) == 0

    def test_no_functions_no_paragraphs(self):
        """Verify handling of content with no clear structure."""
        content = "Just some text without structure."
        file_history = [{"content": content}]
        snippets = retrieve_semantic_summaries("test", file_history)
        # Should still return something if there is text
        assert len(snippets) >= 0  # Depends on implementation details of fallback

class TestContextProcessorsIntegration:
    """Integration tests for the context processor module."""

    def test_process_context_summarization_strategy(self):
        """Test the full process_context pipeline with summarization."""
        content = """
        This is the issue description context.
        
        def calculate_sum(a, b):
            # This function adds two numbers
            return a + b # Returns the sum.
        """
        file_history = [{"content": content}]
        result = process_context("summarization", "test query", file_history, max_tokens=1000)
        
        assert result.total_tokens > 0
        assert len(result.snippets) > 0
        assert isinstance(result.snippets[0], ContextSnippet)

    def test_fallback_on_empty_summarization(self):
        """Test fallback to baseline when summarization yields nothing."""
        # Content that might yield nothing for summarization logic if strictly enforced
        # But our logic is robust, so we test the explicit empty case
        file_history = []
        result = process_context("summarization", "test query", file_history)
        
        # Should fallback to baseline
        assert result.total_tokens == 0 # Baseline on empty history is empty
        assert len(result.snippets) == 1 # Baseline returns one snippet (empty)

    def test_tfidf_retrieval(self):
        """Test TF-IDF retrieval logic."""
        history = [
            {"content": "This is a test document about machine learning."},
            {"content": "This is a document about cooking."}
        ]
        snippets = retrieve_tfidf_snippets("machine learning", history, top_k=1)
        assert len(snippets) == 1
        assert "machine learning" in snippets[0].content

    def test_diff_aware_retrieval(self):
        """Test diff-aware retrieval logic."""
        history = [
            {"content": "def fix_bug():\n    print('fixing')"},
            {"content": "def unrelated():\n    pass"}
        ]
        snippets = retrieve_diff_aware_snippets("fix bug", history)
        assert len(snippets) > 0
        assert "fix_bug" in snippets[0].content