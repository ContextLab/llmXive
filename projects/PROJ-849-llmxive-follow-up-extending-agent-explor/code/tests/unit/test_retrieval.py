import pytest
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from src.lib.tool_loader import load_tool_mapping, ToolLoaderError
from src.lib import config


class TestBM25RetrievalEdgeCases:
    """Unit tests for BM25 retrieval edge cases, specifically zero results."""

    def test_bm25_zero_results_empty_query(self):
        """Test that BM25 returns an empty list when the query contains no tokens."""
        # Create a simple BM25 index with some tool descriptions
        tool_descriptions = [
            ["calculator", "performs", "mathematical", "operations"],
            ["web", "search", "finds", "information", "online"],
            ["code", "interpreter", "executes", "python", "code"],
        ]
        bm25 = BM25Okapi(tool_descriptions)

        # Query with stop words only or empty string results in zero tokens
        empty_query = []
        results = bm25.get_scores(empty_query)

        # All scores should be 0.0
        assert all(score == 0.0 for score in results), "Empty query should yield zero scores"

    def test_bm25_zero_results_unmatched_terms(self):
        """Test that BM25 returns zero scores for completely unmatched terms."""
        tool_descriptions = [
            ["calculator", "performs", "mathematical", "operations"],
            ["web", "search", "finds", "information", "online"],
            ["code", "interpreter", "executes", "python", "code"],
        ]
        bm25 = BM25Okapi(tool_descriptions)

        # Query with terms that do not exist in the corpus
        unmatched_query = ["quantum", "entanglement", "superposition"]
        results = bm25.get_scores(unmatched_query)

        # All scores should be 0.0 because no terms match the corpus
        assert all(score == 0.0 for score in results), "Unmatched query should yield zero scores"

    def test_bm25_zero_results_with_custom_index(self):
        """Test zero results scenario using the actual tool mapping loader."""
        # Load the real tool mapping
        try:
            tool_map = load_tool_mapping()
        except ToolLoaderError:
            pytest.skip("Tool mapping file not found, skipping integration-style edge case test")

        if not tool_map:
            pytest.skip("Tool mapping is empty, cannot test retrieval")

        # Tokenize the tool descriptions
        tokenized_corpus = []
        for tool_name, tool_info in tool_map.items():
            description = tool_info.get("description", "")
            # Simple tokenization: split by whitespace and lowercase
            tokens = description.lower().split()
            if tokens:
                tokenized_corpus.append(tokens)

        if not tokenized_corpus:
            pytest.skip("No tokenized descriptions available in tool map")

        bm25 = BM25Okapi(tokenized_corpus)

        # Query with terms guaranteed not to be in the tool descriptions
        # Using very specific, unlikely terms
        unlikely_query = ["xyz123", "nonexistent", "placeholder"]
        scores = bm25.get_scores(unlikely_query)

        # Verify that we get zero scores for all documents
        assert all(score == 0.0 for score in scores), "Unlikely query terms should result in zero scores"

    def test_retrieval_service_zero_results_handling(self):
        """Test that the retrieval service handles zero results gracefully."""
        from src.services.retrieval_service import RetrievalService, create_retrieval_service

        # Create a retrieval service
        try:
            service = create_retrieval_service()
        except ToolLoaderError:
            pytest.skip("Tool mapping file not found, skipping service test")

        # Query with terms that likely won't match
        query = "xyz123_nonexistent_query_terms"
        results = service.retrieve_top_tools(query, top_k=5)

        # When no matches are found, the service should return an empty list
        # or a list with zero-scored items depending on implementation.
        # Based on standard BM25 behavior with zero scores, we expect empty or all-zero.
        if isinstance(results, list):
            if len(results) > 0:
                # If items are returned, their scores must be 0.0
                for item in results:
                    assert item.get("score", 0.0) == 0.0, "Zero result items should have 0.0 score"
            # It is also acceptable to return an empty list for zero results
        else:
            pytest.fail(f"Unexpected return type from retrieve_top_tools: {type(results)}")