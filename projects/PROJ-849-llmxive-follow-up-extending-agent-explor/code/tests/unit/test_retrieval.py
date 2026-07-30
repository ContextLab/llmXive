"""
Unit tests for retrieval service.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from services.retrieval_service import RetrievalService

class TestRetrievalService:
    @patch('services.retrieval_service.load_tool_mapping')
    def test_initialize_success(self, mock_load):
        mock_load.return_value = [
            {"tool_descriptions": ["tool A", "tool B"]},
            {"tool_descriptions": ["tool C"]}
        ]
        service = RetrievalService()
        service.initialize()
        assert service._initialized is True
        assert len(service.tool_corpus) == 3 # 3 descriptions total

    @patch('services.retrieval_service.load_tool_mapping')
    def test_retrieve_top_tools(self, mock_load):
        mock_load.return_value = [
            {"tool_descriptions": ["math calculator", "graph plotter"]}
        ]
        service = RetrievalService()
        service.initialize()
        
        # Query for "math"
        results = service.retrieve_top_tools("math calculator", top_k=1)
        assert len(results) > 0
        assert "math" in results[0][0][0].lower() or "calculator" in results[0][0][0].lower()
