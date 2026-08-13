"""
Unit tests for the verify_structure module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from setup.verify_structure import check_directory_writable, run_ls_recursive

class TestCheckDirectoryWritable:
    def test_existing_writable_directory(self, tmp_path):
        """Test that an existing writable directory returns True."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        assert check_directory_writable(test_dir) is True

    def test_nonexistent_directory(self, tmp_path):
        """Test that a non-existent directory returns False."""
        non_existent = tmp_path / "non_existent"
        
        assert check_directory_writable(non_existent) is False

    def test_file_instead_of_directory(self, tmp_path):
        """Test that a file path returns False."""
        test_file = tmp_path / "test_file.txt"
        test_file.touch()
        
        assert check_directory_writable(test_file) is False

    @patch('pathlib.Path.touch')
    def test_unwritable_directory(self, mock_touch, tmp_path):
        """Test that an unwritable directory returns False."""
        test_dir = tmp_path / "unwritable"
        test_dir.mkdir()
        
        mock_touch.side_effect = PermissionError("Permission denied")
        
        assert check_directory_writable(test_dir) is False

class TestRunLsRecursive:
    def test_creates_output_file(self, tmp_path):
        """Test that run_ls_recursive creates the output file."""
        output_path = tmp_path / "output.txt"
        
        with patch('setup.verify_structure.PROJECT_ROOT', tmp_path):
            result = run_ls_recursive(output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_output_contains_directories(self, tmp_path):
        """Test that the output file contains directory listings."""
        # Create some test directories
        (tmp_path / "test1").mkdir()
        (tmp_path / "test1" / "subdir").mkdir()
        (tmp_path / "test2").mkdir()
        
        output_path = tmp_path / "output.txt"
        
        with patch('setup.verify_structure.PROJECT_ROOT', tmp_path):
            run_ls_recursive(output_path)
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "test1" in content
        assert "test2" in content
        assert "subdir" in content

    def test_invalid_output_path(self, tmp_path):
        """Test handling of invalid output path."""
        invalid_path = tmp_path / "nonexistent_dir" / "output.txt"
        
        with patch('setup.verify_structure.PROJECT_ROOT', tmp_path):
            result = run_ls_recursive(invalid_path)
        
        # Should create parent directories
        assert result is True
        assert invalid_path.exists()