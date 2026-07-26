"""
Tests for the verify_linting module (T003b).

These tests verify that the linting configuration verification script:
1. Creates a dummy __init__.py if no code exists
2. Runs black and flake8 commands
3. Appends results to data/checksums.txt
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest

# We need to add the code directory to the path to import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_linting import run_command, create_dummy_init_if_needed, append_to_checksums_file


class TestRunCommand:
    """Tests for the run_command function."""

    def test_run_command_success(self):
        """Test that run_command returns True for a successful command."""
        # Use a command that should always succeed
        result = run_command(["echo", "hello"], "Test command")
        assert result is True

    def test_run_command_failure(self):
        """Test that run_command returns False for a failing command."""
        # Use a command that should fail (exit code 1)
        result = run_command(["sh", "-c", "exit 1"], "Failing command")
        assert result is False

    def test_run_command_file_not_found(self):
        """Test that run_command returns False when command is not found."""
        with patch('verify_linting.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            result = run_command(["nonexistent_command"], "Test")
            assert result is False


class TestCreateDummyInitIfNeeded:
    """Tests for the create_dummy_init_if_needed function."""

    def setup_method(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_creates_init_when_no_code(self):
        """Test that __init__.py is created when code/ is empty."""
        code_dir = Path("code")
        code_dir.mkdir()

        create_dummy_init_if_needed()

        init_file = code_dir / "__init__.py"
        assert init_file.exists()
        assert init_file.read_text() == "# Project root package\n"

    def test_does_not_overwrite_existing_init(self):
        """Test that existing __init__.py is not overwritten."""
        code_dir = Path("code")
        code_dir.mkdir()
        init_file = code_dir / "__init__.py"
        init_file.write_text("# Existing content\n")

        create_dummy_init_if_needed()

        assert init_file.read_text() == "# Existing content\n"

    def test_creates_code_dir_if_missing(self):
        """Test that code/ directory is created if it doesn't exist."""
        create_dummy_init_if_needed()

        code_dir = Path("code")
        assert code_dir.exists()
        assert (code_dir / "__init__.py").exists()


class TestAppendToChecksumsFile:
    """Tests for the append_to_checksums_file function."""

    def setup_method(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_creates_file_and_appends(self):
        """Test that the function creates the file and appends content."""
        output_lines = ["Line 1", "Line 2", "Line 3"]
        description = "Test Description"

        append_to_checksums_file(output_lines, description)

        checksums_file = Path("data/checksums.txt")
        assert checksums_file.exists()

        content = checksums_file.read_text()
        assert "Test Description" in content
        assert "Line 1" in content
        assert "Line 2" in content
        assert "Line 3" in content

    def test_appends_to_existing_file(self):
        """Test that content is appended to an existing file."""
        checksums_file = Path("data/checksums.txt")
        checksums_file.parent.mkdir()
        checksums_file.write_text("Existing content\n")

        append_to_checksums_file(["New line"], "Test")

        content = checksums_file.read_text()
        assert "Existing content" in content
        assert "New line" in content


class TestIntegration:
    """Integration tests for the full T003b workflow."""

    def setup_method(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create minimal project structure
        Path("code").mkdir()
        Path("data").mkdir()

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_full_workflow_with_mocked_commands(self):
        """Test the full workflow with mocked black and flake8 commands."""
        from verify_linting import main

        with patch('verify_linting.run_command') as mock_run:
            # Mock both commands to succeed
            mock_run.return_value = True

            result = main()

            # Should call run_command twice (black and flake8)
            assert mock_run.call_count == 2

            # Should return 0 (success)
            assert result == 0

            # Should have created checksums file
            checksums_file = Path("data/checksums.txt")
            assert checksums_file.exists()