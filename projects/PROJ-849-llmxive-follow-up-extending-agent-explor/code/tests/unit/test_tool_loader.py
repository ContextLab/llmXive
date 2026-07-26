"""
Unit tests for the tool_loader module.

These tests verify the strict error handling and validation logic
required by FR-002, ensuring the system halts on missing or empty mappings.
"""
import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.lib.tool_loader import (
    ToolLoaderError,
    load_tool_mapping,
    validate_tool_mapping,
    get_available_tools
)


class TestToolLoader:
    """Test suite for ToolLoader functionality."""

    def test_load_valid_mapping(self, tmp_path):
        """Test loading a valid, non-empty JSON file."""
        valid_data = {
            "tool_a": {"description": "Tool A description"},
            "tool_b": {"description": "Tool B description"}
        }
        file_path = tmp_path / "valid_tools.json"
        file_path.write_text(json.dumps(valid_data))

        result = load_tool_mapping(file_path)
        assert result == valid_data
        assert len(result) == 2

    def test_load_missing_file(self):
        """Test that ToolLoaderError is raised if file does not exist."""
        non_existent_path = Path("/non/existent/path/tools.json")
        
        with pytest.raises(ToolLoaderError) as exc_info:
            load_tool_mapping(non_existent_path)
        
        assert "Tool Mapping Missing" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    def test_load_empty_file(self, tmp_path):
        """Test that ToolLoaderError is raised if file is empty."""
        file_path = tmp_path / "empty_tools.json"
        file_path.write_text("")

        with pytest.raises(ToolLoaderError) as exc_info:
            load_tool_mapping(file_path)
        
        assert "Tool Mapping Missing" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_load_whitespace_only_file(self, tmp_path):
        """Test that ToolLoaderError is raised if file contains only whitespace."""
        file_path = tmp_path / "whitespace_tools.json"
        file_path.write_text("   \n\n   ")

        with pytest.raises(ToolLoaderError) as exc_info:
            load_tool_mapping(file_path)
        
        assert "Tool Mapping Missing" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_load_invalid_json(self, tmp_path):
        """Test that ToolLoaderError is raised for invalid JSON syntax."""
        file_path = tmp_path / "invalid_tools.json"
        file_path.write_text("{ invalid json }")

        with pytest.raises(ToolLoaderError) as exc_info:
            load_tool_mapping(file_path)
        
        assert "Tool Mapping Missing" in str(exc_info.value)
        assert "Invalid JSON" in str(exc_info.value)

    def test_load_non_dict_json(self, tmp_path):
        """Test that ToolLoaderError is raised if root JSON is not a dict."""
        file_path = tmp_path / "list_tools.json"
        file_path.write_text(json.dumps(["tool1", "tool2"]))

        with pytest.raises(ToolLoaderError) as exc_info:
            load_tool_mapping(file_path)
        
        assert "Tool Mapping Missing" in str(exc_info.value)
        assert "Expected a JSON object" in str(exc_info.value)

    def test_load_empty_dict_json(self, tmp_path):
        """Test that ToolLoaderError is raised if root JSON is an empty dict."""
        file_path = tmp_path / "empty_dict_tools.json"
        file_path.write_text(json.dumps({}))

        with pytest.raises(ToolLoaderError) as exc_info:
            load_tool_mapping(file_path)
        
        assert "Tool Mapping Missing" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_validate_valid_mapping(self):
        """Test validation of a valid mapping."""
        valid_mapping = {"tool": {"desc": "test"}}
        assert validate_tool_mapping(valid_mapping) is True

    def test_validate_empty_mapping(self):
        """Test validation of an empty mapping."""
        empty_mapping = {}
        with pytest.raises(ToolLoaderError) as exc_info:
            validate_tool_mapping(empty_mapping)
        
        assert "Validation failed" in str(exc_info.value)
        assert "at least one entry" in str(exc_info.value).lower()

    def test_validate_non_dict(self):
        """Test validation of a non-dict mapping."""
        with pytest.raises(ToolLoaderError) as exc_info:
            validate_tool_mapping(["not", "a", "dict"])
        
        assert "Validation failed" in str(exc_info.value)
        assert "must be a dictionary" in str(exc_info.value).lower()

    def test_get_available_tools(self, tmp_path):
        """Test extracting tool names from a mapping."""
        valid_data = {
            "calculator": {"desc": "calc"},
            "search": {"desc": "search"}
        }
        file_path = tmp_path / "tools.json"
        file_path.write_text(json.dumps(valid_data))

        mapping = load_tool_mapping(file_path)
        tools = get_available_tools(mapping)

        assert set(tools) == {"calculator", "search"}
        assert len(tools) == 2