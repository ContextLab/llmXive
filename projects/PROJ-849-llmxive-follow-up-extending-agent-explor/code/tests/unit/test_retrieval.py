import pytest
import numpy as np
from unittest.mock import Mock, patch
from services.retrieval_service import RetrievalService
from lib.tool_mapper import ToolMapper

class TestRetrievalService:
    @pytest.fixture
    def sample_tool_map(self):
        return {
            "prob1": {"tool_descriptions": ["calculator", "graphing_tool"]},
            "prob2": {"tool_descriptions": ["text_searcher", "code_runner"]}
        }

    def test_init_builds_index(self, sample_tool_map):
        service = RetrievalService(sample_tool_map)
        assert service.bm25_index is not None

    def test_retrieve_tools_returns_top_k(self, sample_tool_map):
        service = RetrievalService(sample_tool_map)
        results = service.retrieve_tools("calculate", top_k=2)
        assert len(results) <= 2
        assert "calculator" in results

    def test_retrieve_tools_empty_query(self, sample_tool_map):
        service = RetrievalService(sample_tool_map)
        results = service.retrieve_tools("")
        assert len(results) == 0

    def test_retrieve_tools_no_index(self):
        # Mock empty tool map
        with patch.object(ToolMapper, '__init__', return_value=None):
            service = RetrievalService({})
            results = service.retrieve_tools("test")
            assert results == []
