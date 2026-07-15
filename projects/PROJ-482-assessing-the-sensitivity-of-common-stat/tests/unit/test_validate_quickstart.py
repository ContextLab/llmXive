"""
Unit tests for the quickstart validation script.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import subprocess

# Import the functions to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from validate_quickstart import (
    check_path_exists,
    check_file_not_empty,
    run_command,
    validate_imports,
    validate_quickstart_paths,
    validate_data_outputs,
    run_pipeline_validation
)

class TestCheckPathExists:
    def test_existing_path(self, tmp_path):
        """Test checking an existing path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert check_path_exists(str(test_file), "test file") is True

    def test_non_existing_path(self):
        """Test checking a non-existing path."""
        assert check_path_exists("/non/existent/path", "test path") is False

class TestCheckFileNotEmpty:
    def test_non_empty_file(self, tmp_path):
        """Test checking a non-empty file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        assert check_file_not_empty(str(test_file), "test file") is True

    def test_empty_file(self, tmp_path):
        """Test checking an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        assert check_file_not_empty(str(test_file), "test file") is False

    def test_non_existing_file(self):
        """Test checking a non-existing file."""
        assert check_file_not_empty("/non/existent/file.txt", "test file") is False

class TestRunCommand:
    @patch('subprocess.run')
    def test_successful_command(self, mock_run):
        """Test running a successful command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        assert run_command(["echo", "test"], "test command") is True

    @patch('subprocess.run')
    def test_failed_command(self, mock_run):
        """Test running a failed command."""
        mock_run.return_value = MagicMock(returncode=1, stdout="output", stderr="error")
        assert run_command(["false"], "test command") is False

    @patch('subprocess.run')
    def test_timeout_command(self, mock_run):
        """Test running a command that times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=1)
        assert run_command(["slow"], "test command") is False

class TestValidateImports:
    @patch('validate_quickstart.__import__')
    def test_all_imports_success(self, mock_import):
        """Test when all imports succeed."""
        mock_import.return_value = MagicMock()
        # Mock the __import__ to always succeed
        with patch('validate_quickstart.__builtins__.__import__', side_effect=mock_import):
            result = validate_imports()
            # This should return True if all imports succeed
            assert result is True

    @patch('validate_quickstart.__import__')
    def test_import_failure(self, mock_import):
        """Test when an import fails."""
        def import_side_effect(name, *args, **kwargs):
            if name == 'nonexistent_module':
                raise ImportError("Module not found")
            return MagicMock()
        
        mock_import.side_effect = import_side_effect
        result = validate_imports()
        # Should return False if any import fails
        assert result is False

class TestValidateQuickstartPaths:
    def test_existing_paths(self, tmp_path):
        """Test validation of existing paths."""
        # Create required structure
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        (tmp_path / "data" / "processed").mkdir()
        
        # Create required files
        (tmp_path / "code" / "config.py").write_text("# config")
        (tmp_path / "code" / "data_generator.py").write_text("# data_generator")
        (tmp_path / "code" / "simulation_engine.py").write_text("# simulation_engine")
        (tmp_path / "code" / "analyzer.py").write_text("# analyzer")
        (tmp_path / "code" / "visualizer.py").write_text("# visualizer")
        (tmp_path / "code" / "main.py").write_text("# main")
        (tmp_path / "quickstart.md").write_text("# quickstart")
        
        # Change to temp directory for testing
        original_dir = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            result = validate_quickstart_paths()
            assert result is True
        finally:
            os.chdir(original_dir)

    def test_missing_paths(self, tmp_path):
        """Test validation when some paths are missing."""
        original_dir = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            result = validate_quickstart_paths()
            assert result is False
        finally:
            os.chdir(original_dir)
