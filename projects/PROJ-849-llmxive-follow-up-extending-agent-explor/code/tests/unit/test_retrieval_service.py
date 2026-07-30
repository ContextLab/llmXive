"""
Unit tests for the Retrieval Service.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.retrieval_service import (
    RetrievalService, 
    RetrievalServiceError, 
    create_retrieval_service,
    retrieve_top_tools
)
from src.lib.tool_mapper import ToolMapperError


class TestRetrievalService:
    """Test cases for RetrievalService."""
    
    @pytest.fixture
    def sample_problems(self):
        """Sample problem data for testing."""
        return [
            {
                'problem_id': 'p1',
                'tool_descriptions': [
                    'calculator: Perform arithmetic operations',
                    'grapher: Plot mathematical functions'
                ]
            },
            {
                'problem_id': 'p2',
                'tool_descriptions': [
                    'statistician: Calculate statistical measures',
                    'solver: Solve equations'
                ]
            }
        ]
    
    @pytest.fixture
    def sample_tool_map_json(self):
        """Sample tool map JSON content."""
        return {
            'problems': [
                {
                    'problem_id': 'p1',
                    'tool_descriptions': ['tool_a', 'tool_b']
                },
                {
                    'problem_id': 'p2',
                    'tool_descriptions': ['tool_c']
                }
            ]
        }
    
    def test_initialization(self):
        """Test service initialization."""
        service = RetrievalService()
        assert service.bm25_index is None
        assert service.tool_descriptions == []
        assert service._built is False
    
    def test_build_index_success(self, sample_problems):
        """Test successful index building."""
        service = RetrievalService()
        service.build_index(sample_problems)
        
        assert service._built is True
        assert service.bm25_index is not None
        assert len(service.tool_descriptions) == 4  # 2 + 2
        assert len(service.tokenized_corpus) == 4
    
    def test_build_index_empty_problems(self):
        """Test index building with empty problems."""
        service = RetrievalService()
        with pytest.raises(RetrievalServiceError):
            service.build_index([])
    
    def test_build_index_no_tool_descriptions(self):
        """Test index building with no tool descriptions."""
        problems = [
            {'problem_id': 'p1'},  # Missing tool_descriptions
            {'problem_id': 'p2', 'tool_descriptions': []}
        ]
        service = RetrievalService()
        with pytest.raises(RetrievalServiceError):
            service.build_index(problems)
    
    def test_retrieve_top_k_empty_query(self, sample_problems):
        """Test retrieval with empty query."""
        service = RetrievalService()
        service.build_index(sample_problems)
        
        tools, scores = service.retrieve_top_k("")
        assert tools == []
        assert scores == []
    
    def test_retrieve_top_k_success(self, sample_problems):
        """Test successful retrieval."""
        service = RetrievalService()
        service.build_index(sample_problems)
        
        tools, scores = service.retrieve_top_k("calculator arithmetic", k=2)
        
        assert len(tools) > 0
        assert len(scores) > 0
        assert len(tools) == len(scores)
        assert all(isinstance(t, str) for t in tools)
        assert all(isinstance(s, float) for s in scores)
    
    def test_retrieve_top_k_not_built(self):
        """Test retrieval before index is built."""
        service = RetrievalService()
        with pytest.raises(RetrievalServiceError):
            service.retrieve_top_k("test query")
    
    def test_get_index_stats(self, sample_problems):
        """Test getting index statistics."""
        service = RetrievalService()
        stats_before = service.get_index_stats()
        assert stats_before['built'] is False
        
        service.build_index(sample_problems)
        stats_after = service.get_index_stats()
        assert stats_after['built'] is True
        assert stats_after['num_documents'] == 4
    
    def test_create_retrieval_service(self):
        """Test factory function."""
        service = create_retrieval_service()
        assert isinstance(service, RetrievalService)
    
    def test_retrieve_top_tools_multiple_problems(self, sample_problems):
        """Test retrieving tools for multiple problems."""
        traces = ["calculate sum", "plot graph"]
        
        results = retrieve_top_tools(sample_problems, traces, k=2)
        
        assert len(results) == 2
        assert results[0]['problem_id'] == 'p1'
        assert results[1]['problem_id'] == 'p2'
        assert 'retrieved_tools' in results[0]
        assert 'tool_scores' in results[0]
        assert 'num_tools_retrieved' in results[0]
    
    def test_retrieve_top_tools_length_mismatch(self, sample_problems):
        """Test error when problems and traces have different lengths."""
        traces = ["only one trace"]
        
        with pytest.raises(RetrievalServiceError):
            retrieve_top_tools(sample_problems, traces, k=2)