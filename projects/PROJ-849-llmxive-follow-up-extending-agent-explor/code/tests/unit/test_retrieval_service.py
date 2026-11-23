"""
Unit tests for RetrievalService.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code/src to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.services.retrieval_service import RetrievalService, RetrievalServiceError
from src.lib.tool_mapper import ToolMapperError

class TestRetrievalService:
    """Tests for RetrievalService class."""

    @pytest.fixture
    def mock_tool_descriptions(self):
        """Mock tool descriptions for testing."""
        return [
            "Calculator tool for performing arithmetic operations",
            "Code interpreter for running Python scripts",
            "Web search tool for finding information online",
            "Data visualization tool for creating charts",
            "Text analysis tool for natural language processing"
        ]

    @pytest.fixture
    def mock_tool_mapper(self, mock_tool_descriptions):
        """Mock the tool mapper to return test data."""
        with patch('src.services.retrieval_service.get_tool_descriptions') as mock_get:
            mock_get.return_value = mock_tool_descriptions
            yield mock_get

    @pytest.fixture
    def mock_all_problem_ids(self):
        """Mock all problem IDs."""
        with patch('src.services.retrieval_service.get_all_problem_ids') as mock_ids:
            mock_ids.return_value = ["problem_001", "problem_002"]
            yield mock_ids

    def test_build_index_success(self, mock_tool_mapper, mock_tool_descriptions):
        """Test successful index building."""
        service = RetrievalService()
        service.build_index(problem_id="test_problem")

        assert service._is_built is True
        assert service.bm25_index is not None
        assert len(service.tool_corpus) == len(mock_tool_descriptions)

    def test_build_index_empty_corpus(self):
        """Test building index with empty corpus."""
        with patch('src.services.retrieval_service.get_tool_descriptions') as mock_get:
            mock_get.return_value = []
            service = RetrievalService()
            service.build_index(problem_id="empty_problem")

            assert service._is_built is False
            assert service.bm25_index is None
            assert len(service.tool_corpus) == 0

    def test_retrieve_top_k_success(self, mock_tool_mapper):
        """Test successful retrieval of top-k tools."""
        service = RetrievalService()
        service.build_index(problem_id="test_problem")

        results = service.retrieve_top_k("calculator arithmetic", k=2)

        assert len(results) == 2
        assert isinstance(results[0], tuple)
        assert len(results[0]) == 2
        assert "calculator" in results[0][0].lower() or "arithmetic" in results[0][0].lower()

    def test_retrieve_top_k_empty_query(self, mock_tool_mapper):
        """Test retrieval with empty query."""
        service = RetrievalService()
        service.build_index(problem_id="test_problem")

        results = service.retrieve_top_k("", k=2)
        assert results == []

        results = service.retrieve_top_k("   ", k=2)
        assert results == []

    def test_retrieve_top_k_not_built(self):
        """Test retrieval when index is not built."""
        service = RetrievalService()
        # Do not build index

        results = service.retrieve_top_k("test query", k=2)
        assert results == []

    def test_retrieve_top_k_k_larger_than_corpus(self, mock_tool_mapper):
        """Test retrieval when k is larger than corpus size."""
        service = RetrievalService()
        service.build_index(problem_id="test_problem")

        results = service.retrieve_top_k("calculator", k=100)
        assert len(results) <= len(service.tool_corpus)

    def test_retrieve_top_k_no_matches(self, mock_tool_mapper):
        """Test retrieval when no documents match the query significantly."""
        service = RetrievalService()
        service.build_index(problem_id="test_problem")

        # Use a query that might not match well
        results = service.retrieve_top_k("xyzzy qwerty", k=2)
        # Should still return results, possibly with low scores
        assert len(results) == 2
        # Scores might be 0.0 or very low
        for _, score in results:
            assert isinstance(score, float)

    def test_tokenization(self, mock_tool_mapper):
        """Test internal tokenization method."""
        service = RetrievalService()
        service.build_index(problem_id="test_problem")

        tokens = service._tokenize("Hello, World! This is a TEST.")
        expected_tokens = ["hello", "world", "this", "is", "a", "test"]
        assert tokens == expected_tokens

    def test_get_corpus_stats(self, mock_tool_mapper):
        """Test getting corpus statistics."""
        service = RetrievalService()
        service.build_index(problem_id="test_problem")

        stats = service.get_corpus_stats()

        assert "corpus_size" in stats
        assert "is_built" in stats
        assert "average_doc_length" in stats
        assert stats["corpus_size"] > 0
        assert stats["is_built"] is True

    def test_build_index_with_all_problems(self, mock_tool_mapper, mock_all_problem_ids):
        """Test building index for all problems when no problem_id is specified."""
        # Mock get_tool_descriptions to be called multiple times
        with patch('src.services.retrieval_service.get_tool_descriptions') as mock_get:
            mock_get.side_effect = [
                ["tool1", "tool2"], # problem_001
                ["tool3"]           # problem_002
            ]
            
            service = RetrievalService()
            service.build_index() # No problem_id

            assert service._is_built is True
            assert len(service.tool_corpus) == 3
            assert len(service.tool_ids) == 3

    def test_retrieval_service_error_on_build_failure(self):
        """Test that RetrievalServiceError is raised on build failure."""
        with patch('src.services.retrieval_service.get_tool_descriptions') as mock_get:
            mock_get.side_effect = ToolMapperError("Mapping file not found")
            
            service = RetrievalService()
            with pytest.raises(RetrievalServiceError):
                service.build_index(problem_id="fail_problem")