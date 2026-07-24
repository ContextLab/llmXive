import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import extract_bug_fix_description, extract_changed_lines

class TestExtractBugFixDescription:
    """Tests for extract_bug_fix_description function in data_loader.py"""

    def test_extract_with_full_fields(self):
        """Test extraction when all fields are present"""
        data = {
            'project': ['junit'],
            'bug_id': ['123'],
            'description': ['AssertionError when input is null'],
            'commit_msg': ['Fixed null pointer']
        }
        df = pd.DataFrame(data)
        
        prompt = extract_bug_fix_description(df, 0)
        
        assert "Bug ID: 123" in prompt
        assert "Project: junit" in prompt
        assert "AssertionError when input is null" in prompt
        assert prompt.startswith("Bug ID:")
        assert "|" in prompt

    def test_extract_fallback_to_commit_msg(self):
        """Test that commit_msg is used when description is empty/NaN"""
        data = {
            'project': ['mockito'],
            'bug_id': ['456'],
            'description': [None],
            'commit_msg': ['Refactored mock creation logic']
        }
        df = pd.DataFrame(data)
        
        prompt = extract_bug_fix_description(df, 0)
        
        assert "Refactored mock creation logic" in prompt
        assert "description" not in prompt or "No description" not in prompt

    def test_extract_empty_description_fallback(self):
        """Test fallback when description is empty string"""
        data = {
            'project': ['commons-lang'],
            'bug_id': ['789'],
            'description': [''],
            'commit_msg': ['Updated string utilities']
        }
        df = pd.DataFrame(data)
        
        prompt = extract_bug_fix_description(df, 0)
        
        assert "Updated string utilities" in prompt

    def test_extract_no_description_or_commit(self):
        """Test behavior when both description and commit_msg are missing"""
        data = {
            'project': ['unknown'],
            'bug_id': ['999'],
            'description': [None],
            'commit_msg': [None]
        }
        df = pd.DataFrame(data)
        
        prompt = extract_bug_fix_description(df, 0)
        
        assert "No description available" in prompt

    def test_extract_invalid_row_index(self):
        """Test that IndexError is raised for out-of-bounds index"""
        data = {
            'project': ['test'],
            'bug_id': ['1'],
            'description': ['test desc']
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(IndexError):
            extract_bug_fix_description(df, 100)

    def test_extract_negative_row_index(self):
        """Test that IndexError is raised for negative index"""
        data = {
            'project': ['test'],
            'bug_id': ['1'],
            'description': ['test desc']
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(IndexError):
            extract_bug_fix_description(df, -1)

    def test_extract_format_structure(self):
        """Verify the exact format of the prompt string"""
        data = {
            'project': ['proj'],
            'bug_id': ['1'],
            'description': ['desc']
        }
        df = pd.DataFrame(data)
        
        prompt = extract_bug_fix_description(df, 0)
        
        # Check specific format requirements
        parts = prompt.split(" | ")
        assert len(parts) == 3
        assert parts[0] == "Bug ID: 1"
        assert parts[1] == "Project: proj"
        assert parts[2] == "Description: desc"

class TestExtractChangedLines:
    """Tests for extract_changed_lines (placeholder)"""

    def test_extract_changed_lines_returns_empty_set(self):
        """Placeholder test: currently returns empty set"""
        df = pd.DataFrame({'a': [1, 2]})
        result = extract_changed_lines(df)
        assert result == set()