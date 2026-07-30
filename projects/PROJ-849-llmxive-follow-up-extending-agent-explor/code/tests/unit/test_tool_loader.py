"""
Unit tests for tool mapper.
"""
import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from lib.tool_mapper import load_tool_mapping, extract_tool_descriptions, ToolMapperError

class TestToolLoader:
    def test_extract_tool_descriptions_valid(self):
        data = {"tool_descriptions": ["tool1", "tool2"]}
        result = extract_tool_descriptions(data)
        assert result == ["tool1", "tool2"]

    def test_extract_tool_descriptions_missing(self):
        data = {"other_key": "value"}
        with pytest.raises(ToolMapperError):
            extract_tool_descriptions(data)
