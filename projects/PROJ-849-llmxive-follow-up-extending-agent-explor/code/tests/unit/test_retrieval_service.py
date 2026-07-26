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
from src.lib.tool_loader import ToolLoaderError


class TestRetrievalService:
    """Tests for the RetrievalService class."""

    @pytest.fixture
    def mock_tool_mapping(self):
        """Create a mock tool mapping dictionary."""
        return {
            "tool_1": {
                "description": "Calculate the sum of two numbers.",
                "parameters": {"a": "int", "b": "int"}
            },
            "tool_2": {
                "description": "Find the maximum value in a list.",
                "parameters": {"lst": "list"}
            },
            "tool_3": {
                "description": "Convert temperature from Celsius to Fahrenheit.",
                "parameters": {"celsius": "float"}
            },
            "tool_4": {
                "description": "Calculate the area of a circle given radius.",
                "parameters": {"radius": "float"}
            }
        }

    @pytest.fixture
    def temp_tool_file(self, mock_tool_mapping):
        """Create a temporary file with tool mapping."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(mock_tool_mapping, f)
            f.flush()
            yield f.name
        Path(f.name).unlink()

    def test_init(self, temp_tool_file):
        """Test initialization of RetrievalService."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        assert service.tool_map_path == temp_tool_file
        assert service.bm25_index is None
        assert service.tool_descriptions == []
        assert service._index_built is False

    def test_build_index_success(self, temp_tool_file):
        """Test successful index building."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        service.build_index()

        assert service._index_built is True
        assert service.bm25_index is not None
        assert len(service.tool_descriptions) == 4
        assert len(service.tool_ids) == 4
        assert "tool_1" in service.tool_ids

    def test_build_index_empty_mapping(self, temp_tool_file):
        """Test build_index with empty mapping."""
        # Create a temp file with empty dict
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({}, f)
            empty_file = f.name

        try:
            service = RetrievalService(tool_map_path=empty_file)
            with pytest.raises(RetrievalServiceError) as exc_info:
                service.build_index()
            assert "empty or invalid" in str(exc_info.value).lower()
        finally:
            Path(empty_file).unlink()

    def test_build_index_missing_file(self):
        """Test build_index with non-existent file."""
        service = RetrievalService(tool_map_path="/nonexistent/path.json")
        with pytest.raises(RetrievalServiceError) as exc_info:
            service.build_index()
        assert "Failed to load tool mapping" in str(exc_info.value)

    def test_retrieve_without_index(self, temp_tool_file):
        """Test retrieve method before index is built."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        with pytest.raises(RetrievalServiceError) as exc_info:
            service.retrieve("calculate sum")
        assert "index has not been built" in str(exc_info.value).lower()

    def test_retrieve_success(self, temp_tool_file):
        """Test successful retrieval."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        service.build_index()

        results = service.retrieve("calculate sum", top_k=2)

        assert len(results) == 2
        assert isinstance(results, list)
        assert all("tool_id" in r for r in results)
        assert all("description" in r for r in results)
        assert all("score" in r for r in results)

        # The first result should be the one about "sum"
        assert "sum" in results[0]["description"].lower()

    def test_retrieve_empty_query(self, temp_tool_file):
        """Test retrieval with empty query."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        service.build_index()

        results = service.retrieve("", top_k=2)
        assert results == []

    def test_retrieve_top_k_larger_than_available(self, temp_tool_file):
        """Test retrieval when top_k > available tools."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        service.build_index()

        results = service.retrieve("calculate", top_k=10)
        assert len(results) == 4  # Only 4 tools available

    def test_tokenize(self, temp_tool_file):
        """Test tokenization logic."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        service.build_index()

        tokens = service._tokenize("Calculate the SUM of two numbers!")
        assert "calculate" in tokens
        assert "sum" in tokens
        assert "numbers" in tokens
        assert "!" not in tokens

    def test_create_retrieval_service(self, temp_tool_file):
        """Test factory function."""
        with patch('src.services.retrieval_service.RetrievalService') as MockService:
            mock_instance = MagicMock()
            MockService.return_value = mock_instance

            create_retrieval_service()

            MockService.assert_called_once()
            mock_instance.build_index.assert_called_once()

    def test_retrieve_top_tools_convenience(self, temp_tool_file):
        """Test convenience function."""
        with patch('src.services.retrieval_service.RetrievalService') as MockService:
            mock_instance = MagicMock()
            MockService.return_value = mock_instance
            mock_instance.retrieve.return_value = [{"tool_id": "test"}]

            result = retrieve_top_tools("query", top_k=3, tool_map_path=temp_tool_file)

            MockService.assert_called_once_with(tool_map_path=temp_tool_file)
            mock_instance.build_index.assert_called_once()
            mock_instance.retrieve.assert_called_once_with("query", 3)
            assert result == [{"tool_id": "test"}]

    def test_get_tool_centroid(self, temp_tool_file):
        """Test centroid retrieval (placeholder)."""
        service = RetrievalService(tool_map_path=temp_tool_file)
        service.build_index()

        centroid = service.get_tool_centroid("calculate sum", top_k=2)
        assert centroid is not None
        assert isinstance(centroid, list)
        assert len(centroid) == 2
        assert all(isinstance(desc, str) for desc in centroid)