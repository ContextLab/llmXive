"""
Tests for the quickstart validation script.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import subprocess

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from validation.validate_quickstart import (
    check_file_exists,
    check_directory_exists,
    run_command,
    validate_project_structure,
    validate_quickstart_commands,
    main
)

class TestFileChecks:
    def test_check_file_exists_found(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert check_file_exists(test_file, "test file") is True

    def test_check_file_exists_missing(self, tmp_path):
        test_file = tmp_path / "missing.txt"
        assert check_file_exists(test_file, "test file") is False

    def test_check_directory_exists_found(self, tmp_path):
        assert check_directory_exists(tmp_path, "test dir") is True

    def test_check_directory_exists_missing(self, tmp_path):
        missing_dir = tmp_path / "missing"
        assert check_directory_exists(missing_dir, "test dir") is False

    def test_check_directory_exists_not_dir(self, tmp_path):
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        assert check_directory_exists(test_file, "test dir") is False

class TestRunCommand:
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        output_file = tmp_path / "output.txt"
        output_file.touch()

        result = run_command(
            ["echo", "test"],
            "test command",
            [output_file]
        )
        assert result is True

    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")

        result = run_command(
            ["false"],
            "failing command",
            []
        )
        assert result is False

    @patch('subprocess.run')
    def test_run_command_missing_output(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        missing_output = tmp_path / "missing.txt"

        result = run_command(
            ["echo", "test"],
            "test command",
            [missing_output]
        )
        assert result is False

class TestValidationIntegration:
    def test_main_returns_zero_on_success(self, tmp_path, monkeypatch):
        # Mock the config functions to use tmp_path
        from validation import validate_quickstart
        monkeypatch.setattr(validate_quickstart, 'PROJECT_ROOT', tmp_path)

        # Create minimal required structure
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "stimuli").mkdir()
        (tmp_path / "data" / "stimuli_metadata").mkdir()
        (tmp_path / "data" / "processed").mkdir()
        (tmp_path / "requirements.txt").touch()
        (tmp_path / "README.md").touch()

        # Mock the command validation to return True
        with patch.object(validate_quickstart, 'validate_quickstart_commands', return_value=True):
            result = main()
            assert result == 0

    def test_main_returns_one_on_failure(self, tmp_path, monkeypatch):
        from validation import validate_quickstart
        monkeypatch.setattr(validate_quickstart, 'PROJECT_ROOT', tmp_path)

        # Create minimal structure but fail command validation
        with patch.object(validate_quickstart, 'validate_quickstart_commands', return_value=False):
            result = main()
            assert result == 1
