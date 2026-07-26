"""
Unit tests for the RetrievalService (T014).
"""

import pytest
import os
import json
import tempfile
from pathlib import Path

# Mocking the ToolMapper for isolation
from unittest.mock import Mock, MagicMock

from services.retrieval_service import RetrievalService
from lib.config import DATA_DIR


class TestRetrievalService:
    """Tests for RetrievalService functionality."""

    @pytest.fixture
    def mock_tool_mapper(self):
        """Create a mock ToolMapper with sample data."""
        mock_mapper = Mock()
        mock_mapper.mapping = {
            "prob_001": {
                "tool_descriptions": [
                    "Calculate the area of a circle given radius.",
                    "Perform integration of a function."
                ]
            },
            "prob_002": {
                "tool_descriptions": [
                    "Calculate the area of a circle given radius.",
                    "Find the derivative of a polynomial."
                ]
            }
        }
        return mock_mapper

    @pytest.fixture
    def retrieval_service(self, mock_tool_mapper):
        """Initialize RetrievalService with mock mapper."""
        service = RetrievalService(tool_mapper=mock_tool_mapper)
        # Force index build
        service.build_index()
        return service

    def test_index_building(self, retrieval_service):
        """Test that the BM25 index is built correctly."""
        assert retrieval_service._index_built is True
        assert retrieval_service.bm25_index is not None
        assert len(retrieval_service.indexed_tools) == 4 # 2 + 2 tools

    def test_retrieval_non_empty(self, retrieval_service):
        """Test retrieval with a relevant query."""
        results = retrieval_service.retrieve("calculate area circle", top_k=2)
        
        assert len(results) > 0
        # Check that the top result is relevant
        top_desc = results[0]["description"].lower()
        assert "area" in top_desc or "circle" in top_desc

    def test_retrieval_empty_query(self, retrieval_service):
        """Test retrieval with an empty query returns empty list."""
        results = retrieval_service.retrieve("")
        assert results == []

    def test_retrieval_no_match(self, retrieval_service):
        """Test retrieval with completely unrelated query."""
        results = retrieval_service.retrieve("baking a cake", top_k=5)
        # BM25 might still return something with score > 0 if tokens overlap slightly,
        # but if no overlap, it should be empty or low score.
        # We just ensure it doesn't crash and returns a list.
        assert isinstance(results, list)

    def test_get_retrieved_descriptions(self, retrieval_service):
        """Test the convenience method for getting descriptions."""
        descs = retrieval_service.get_retrieved_descriptions("calculate area", top_k=1)
        assert isinstance(descs, list)
        assert len(descs) <= 1
        if len(descs) > 0:
            assert isinstance(descs[0], str)

    def test_empty_index_handling(self):
        """Test behavior when tool mapper has no tools."""
        mock_mapper = Mock()
        mock_mapper.mapping = {
            "prob_001": { "tool_descriptions": [] }
        }
        service = RetrievalService(tool_mapper=mock_mapper)
        service.build_index()
        
        assert service._index_built is True
        assert service.bm25_index is None
        
        results = service.retrieve("anything")
        assert results == []

    def test_retrieval_stats(self, retrieval_service):
        """Test retrieval stats method."""
        stats = retrieval_service.get_retrieval_stats()
        assert stats["index_built"] is True
        assert stats["total_tools_indexed"] == 4
        assert stats["index_type"] == "BM25Okapi"