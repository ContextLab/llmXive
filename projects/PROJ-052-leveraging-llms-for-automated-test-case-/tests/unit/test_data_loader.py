"""
Unit tests for data_loader module, specifically for extract_changed_lines.
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_loader import extract_changed_lines, load_defects4j_data

class TestExtractChangedLines:
    """Tests for the extract_changed_lines function."""

    def test_extract_changed_lines_creates_output_file(self, tmp_path, monkeypatch):
        """Test that extract_changed_lines creates the expected output file."""
        # Mock the data loading
        mock_df = pd.DataFrame({
            'project': ['test_project'],
            'version': ['1.0'],
            'diff': [
                "@@ -10,5 +10,7 @@\n"
                "-old line\n"
                "+new line\n"
                "+another line\n"
            ]
        })

        # Create a temporary data directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Mock get_data_dir to return our temp directory
        def mock_get_data_dir():
            return str(data_dir)

        monkeypatch.setattr('data_loader.get_data_dir', mock_get_data_dir)
        
        # Mock load_defects4j_data
        with patch('data_loader.load_defects4j_data', return_value=mock_df):
            result = extract_changed_lines()

        # Check that output file was created
        output_file = data_dir / "changed_lines.json"
        assert output_file.exists()

        # Check that result is correct
        assert "test_project_1.0" in result
        # The mock diff has changes at line 10
        assert 10 in result["test_project_1.0"]

    def test_extract_changed_lines_handles_empty_diff(self, tmp_path, monkeypatch):
        """Test that extract_changed_lines handles empty diff gracefully."""
        mock_df = pd.DataFrame({
            'project': ['test_project'],
            'version': ['1.0'],
            'diff': [None]
        })

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        def mock_get_data_dir():
            return str(data_dir)

        monkeypatch.setattr('data_loader.get_data_dir', mock_get_data_dir)
        
        with patch('data_loader.load_defects4j_data', return_value=mock_df):
            result = extract_changed_lines()

        # Should return empty dict for projects with no diff
        assert len(result) == 0

    def test_extract_changed_lines_parses_multiple_hunks(self, tmp_path, monkeypatch):
        """Test parsing of multiple hunks in diff."""
        mock_df = pd.DataFrame({
            'project': ['test_project'],
            'version': ['1.0'],
            'diff': [
                "@@ -10,5 +10,7 @@\n"
                "-old line\n"
                "+new line\n"
                "@@ -20,3 +20,5 @@\n"
                "-another old\n"
                "+another new\n"
                "+yet another\n"
            ]
        })

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        def mock_get_data_dir():
            return str(data_dir)

        monkeypatch.setattr('data_loader.get_data_dir', mock_get_data_dir)
        
        with patch('data_loader.load_defects4j_data', return_value=mock_df):
            result = extract_changed_lines()

        # Should have lines from both hunks
        assert "test_project_1.0" in result
        changed_lines = result["test_project_1.0"]
        assert 10 in changed_lines  # From first hunk
        assert 20 in changed_lines  # From second hunk

    def test_extract_changed_lines_missing_columns(self, tmp_path, monkeypatch):
        """Test that missing columns raise ValueError."""
        mock_df = pd.DataFrame({
            'project': ['test_project'],
            'version': ['1.0']
            # Missing 'diff' column
        })

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        def mock_get_data_dir():
            return str(data_dir)

        monkeypatch.setattr('data_loader.get_data_dir', mock_get_data_dir)
        
        with patch('data_loader.load_defects4j_data', return_value=mock_df):
            with pytest.raises(ValueError, match="Missing required columns"):
                extract_changed_lines()

    def test_extract_changed_lines_output_format(self, tmp_path, monkeypatch):
        """Test that output is valid JSON with correct structure."""
        mock_df = pd.DataFrame({
            'project': ['project_a', 'project_b'],
            'version': ['1.0', '2.0'],
            'diff': [
                "@@ -5,2 +5,4 @@\n+line1\n+line2\n",
                "@@ -10,1 +10,3 @@\n+line3\n"
            ]
        })

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        def mock_get_data_dir():
            return str(data_dir)

        monkeypatch.setattr('data_loader.get_data_dir', mock_get_data_dir)
        
        with patch('data_loader.load_defects4j_data', return_value=mock_df):
            result = extract_changed_lines()

        # Verify JSON structure
        assert isinstance(result, dict)
        assert "project_a_1.0" in result
        assert "project_b_2.0" in result
        assert isinstance(result["project_a_1.0"], list)
        assert isinstance(result["project_b_2.0"], list)
        
        # Verify lines are integers
        for lines in result.values():
            for line in lines:
                assert isinstance(line, int)