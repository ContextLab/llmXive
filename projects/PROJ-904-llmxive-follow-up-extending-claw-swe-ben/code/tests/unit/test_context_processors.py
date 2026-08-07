import pytest
import math
from unittest.mock import patch, MagicMock
from data.context_processors import (
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    retrieve_semantic_summaries,
    process_context
)
from config import ContextConfiguration, StrategyType

class TestContextProcessors:
    def test_tfidf_retrieval(self):
        docs = [
            {"file_path": "a.py", "content": "def foo(): pass"},
            {"file_path": "b.py", "content": "def bar(): return 1"}
        ]
        results = retrieve_tfidf_snippets("foo", docs, top_k=1)
        assert len(results) > 0
        assert "foo" in results[0].content

    def test_fallback_logic(self):
        # Test that process_context falls back to naive if strategy returns empty
        result = process_context("query", [], strategy="tfidf")
        assert result.strategy == "naive" or len(result.snippets) > 0