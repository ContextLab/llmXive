"""
Unit tests for the Tool Mapper module (T006).
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

# Import the module under test
# Adjust import path based on project structure (code/src/)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from lib.tool_mapper import (
    load_tool_mapping,
    get_tool_descriptions,
    ToolMapperError,
    ERR_TOOL_MAPPING_MISSING
)


@pytest.fixture
def valid_mapping_data():
    """Fixture providing valid mapping data."""
    return {
        "default_tools": {
            "tool_descriptions": [
                "Use Python for arithmetic calculations.",
                "Use Python to parse text."
            ]
        },
        "problem_specific": {
            "prob_001": {
                "tool_descriptions": [
                    "Use Python for geometry.",
                    "Use Python for algebra."
                ]
            },
            "prob_002": {
                "tool_descriptions": []  # Empty list is valid
            }
        }
    }


@pytest.fixture
def temp_json_file(valid_mapping_data):
    """Creates a temporary JSON file with valid mapping data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_mapping_data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


class TestLoadToolMapping:
    def test_load_existing_file(self, temp_json_file):
        """Test loading an existing valid JSON file."""
        data = load_tool_mapping(temp_json_file)
        assert "default_tools" in data
        assert "problem_specific" in data

    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises ToolMapperError."""
        with pytest.raises(ToolMapperError) as exc_info:
            load_tool_mapping("nonexistent_path.json")
        assert ERR_TOOL_MAPPING_MISSING in str(exc_info.value)

    def test_load_invalid_json(self):
        """Test that loading invalid JSON raises ToolMapperError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(ToolMapperError) as exc_info:
                load_tool_mapping(temp_path)
            assert ERR_TOOL_MAPPING_MISSING in str(exc_info.value)
        finally:
            os.unlink(temp_path)


class TestGetToolDescriptions:
    def test_get_problem_specific_tools(self, valid_mapping_data):
        """Test retrieving tools for a problem found in problem_specific."""
        tools = get_tool_descriptions("prob_001", mapping_data=valid_mapping_data)
        assert len(tools) == 2
        assert "Use Python for geometry." in tools

    def test_get_default_tools(self, valid_mapping_data):
        """Test retrieving default tools when problem not in specific."""
        tools = get_tool_descriptions("prob_999", mapping_data=valid_mapping_data)
        assert len(tools) == 2
        assert "Use Python for arithmetic calculations." in tools

    def test_get_empty_list(self, valid_mapping_data):
        """Test retrieving an empty list of tools is allowed."""
        tools = get_tool_descriptions("prob_002", mapping_data=valid_mapping_data)
        assert tools == []

    def test_missing_problem_descriptions_key(self, valid_mapping_data):
        """Test error when problem exists but lacks tool_descriptions key."""
        # Modify data to have a problem without the key
        bad_data = valid_mapping_data.copy()
        bad_data["problem_specific"]["prob_bad"] = {"other_field": "value"}
        
        with pytest.raises(ToolMapperError) as exc_info:
            get_tool_descriptions("prob_bad", mapping_data=bad_data)
        assert ERR_TOOL_MAPPING_MISSING in str(exc_info.value)

    def test_missing_default_tools_key(self, valid_mapping_data):
        """Test error when problem not found and default_tools lacks key."""
        bad_data = valid_mapping_data.copy()
        del bad_data["default_tools"]["tool_descriptions"]
        
        with pytest.raises(ToolMapperError) as exc_info:
            get_tool_descriptions("prob_999", mapping_data=bad_data)
        assert ERR_TOOL_MAPPING_MISSING in str(exc_info.value)

    def test_non_list_tool_descriptions(self, valid_mapping_data):
        """Test error when tool_descriptions is not a list."""
        bad_data = valid_mapping_data.copy()
        bad_data["default_tools"]["tool_descriptions"] = "string instead of list"
        
        with pytest.raises(ToolMapperError) as exc_info:
            get_tool_descriptions("prob_999", mapping_data=bad_data)
        assert ERR_TOOL_MAPPING_MISSING in str(exc_info.value)
