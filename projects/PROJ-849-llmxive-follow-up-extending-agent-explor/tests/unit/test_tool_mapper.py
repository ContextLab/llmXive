import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from lib.tool_mapper import ToolMapper
from lib.config import ERR_TOOL_MAPPING_MISSING

@pytest.fixture
def temp_mapping_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    tool_dir = tmp_path / "tool_mappings"
    tool_dir.mkdir(parents=True)
    return tool_dir

@pytest.fixture
def valid_mapping_file(temp_mapping_dir):
    """Create a valid tool mapping JSON file."""
    file_path = temp_mapping_dir / "mathvista_tool_map.json"
    data = {
        "default_tools": {
            "tool_descriptions": [
                "Use Python for arithmetic.",
                "Use Python for parsing."
            ]
        },
        "problem_specific": {
            "prob_123": {
                "tool_descriptions": ["Use calculator", "Use grapher"]
            }
        }
    }
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def mapper_with_valid_file(valid_mapping_file):
    """Create a ToolMapper instance pointing to the valid file."""
    return ToolMapper(mapping_path=str(valid_mapping_file))

def test_load_valid_file(mapper_with_valid_file):
    """Test that a valid JSON file loads correctly."""
    data = mapper_with_valid_file.load()
    assert "default_tools" in data
    assert "problem_specific" in data
    assert len(data["default_tools"]["tool_descriptions"]) == 2

def test_get_tool_descriptions_problem_specific(mapper_with_valid_file):
    """Test retrieving descriptions for a specific problem."""
    descs = mapper_with_valid_file.get_tool_descriptions("prob_123")
    assert descs == ["Use calculator", "Use grapher"]

def test_get_tool_descriptions_fallback_default(mapper_with_valid_file):
    """Test fallback to default tools when problem not found."""
    descs = mapper_with_valid_file.get_tool_descriptions("unknown_prob")
    assert descs == ["Use Python for arithmetic.", "Use Python for parsing."]

def test_get_tool_descriptions_missing_raises(mapper_with_valid_file, temp_mapping_dir):
    """Test that missing tool_descriptions raises ValueError with ERR_TOOL_MAPPING_MISSING."""
    # Create a mapping where a problem exists but has no descriptions
    data = {
        "default_tools": {},
        "problem_specific": {
            "bad_prob": {}
        }
    }
    bad_file = temp_mapping_dir / "bad_map.json"
    with open(bad_file, 'w') as f:
        json.dump(data, f)
    
    mapper = ToolMapper(mapping_path=str(bad_file))
    
    with pytest.raises(ValueError) as excinfo:
        mapper.get_tool_descriptions("bad_prob")
    
    assert ERR_TOOL_MAPPING_MISSING in str(excinfo.value)

def test_get_tool_descriptions_null_list_raises(mapper_with_valid_file, temp_mapping_dir):
    """Test that null tool_descriptions raises ValueError."""
    data = {
        "default_tools": {
            "tool_descriptions": None
        },
        "problem_specific": {}
    }
    bad_file = temp_mapping_dir / "bad_map2.json"
    with open(bad_file, 'w') as f:
        json.dump(data, f)
    
    mapper = ToolMapper(mapping_path=str(bad_file))
    
    with pytest.raises(ValueError) as excinfo:
        mapper.get_tool_descriptions("some_prob")
    
    assert ERR_TOOL_MAPPING_MISSING in str(excinfo.value)

def test_file_not_found():
    """Test that FileNotFoundError is raised if the mapping file is missing."""
    mapper = ToolMapper(mapping_path="/nonexistent/path/map.json")
    with pytest.raises(FileNotFoundError):
        mapper.load()
