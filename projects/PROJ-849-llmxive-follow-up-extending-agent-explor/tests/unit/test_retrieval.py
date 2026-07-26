"""
Unit tests for retrieval service.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from services.retrieval_service import RetrievalService

def test_zero_retrieval_edge_case():
    """Test retrieval with empty query."""
    mock_mapping = {
        "problem_types": {
            "math": {
                "tool_descriptions": ["Tool 1", "Tool 2"]
            }
        }
    }
    
    service = RetrievalService(mock_mapping)
    result = service.retrieve_tools("")
    
    assert result == []

def test_retrieval_empty_list():
    """Test retrieval with no tools."""
    mock_mapping = {
        "problem_types": {}
    }
    
    service = RetrievalService(mock_mapping)
    result = service.retrieve_tools("test query")
    
    assert result == []
