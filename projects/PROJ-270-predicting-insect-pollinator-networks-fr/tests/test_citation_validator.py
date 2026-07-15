"""
Tests for the Citation Validator wrapper.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.utils.citation_validator import (
    validate_citations,
    validate_directory,
    run_pre_commit_hook,
    CitationValidationError
)


class TestValidateCitations:
    """Tests for the validate_citations function."""

    def test_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_citations("/non/existent/file.md")

    @patch('code.utils.citation_validator.subprocess.run')
    def test_validation_success(self, mock_run):
        """Should return True when validator returns 0."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b"# Test")
            temp_path = f.name

        try:
            result = validate_citations(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    @patch('code.utils.citation_validator.subprocess.run')
    def test_validation_failure_non_strict(self, mock_run):
        """Should return False when validation fails in non-strict mode."""
        mock_run.return_value = MagicMock(
            returncode=1, 
            stdout="Errors found", 
            stderr="Some error"
        )
        
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b"# Test")
            temp_path = f.name

        try:
            result = validate_citations(temp_path, strict_mode=False)
            assert result is False
        finally:
            os.unlink(temp_path)

    @patch('code.utils.citation_validator.subprocess.run')
    def test_validation_failure_strict(self, mock_run):
        """Should raise CitationValidationError when validation fails in strict mode."""
        mock_run.return_value = MagicMock(
            returncode=1, 
            stdout="Errors found", 
            stderr="Some error"
        )
        
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b"# Test")
            temp_path = f.name

        try:
            with pytest.raises(CitationValidationError):
                validate_citations(temp_path, strict_mode=True)
        finally:
            os.unlink(temp_path)

    @patch('code.utils.citation_validator.subprocess.run')
    def test_validator_not_found(self, mock_run):
        """Should raise FileNotFoundError when validator is not in PATH."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b"# Test")
            temp_path = f.name

        try:
            with pytest.raises(FileNotFoundError):
                validate_citations(temp_path)
        finally:
            os.unlink(temp_path)

    @patch('code.utils.citation_validator.subprocess.run')
    def test_custom_validator_path(self, mock_run):
        """Should use custom validator path when provided."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b"# Test")
            temp_path = f.name

        try:
            custom_path = "/custom/path/to/validator"
            validate_citations(temp_path, validator_path=custom_path)
            
            # Verify the custom path was used in the command
            call_args = mock_run.call_args[0][0]
            assert custom_path in call_args
        finally:
            os.unlink(temp_path)


class TestValidateDirectory:
    """Tests for the validate_directory function."""

    def test_not_a_directory(self):
        """Should raise NotADirectoryError for non-directory path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            with pytest.raises(NotADirectoryError):
                validate_directory(temp_path)
        finally:
            os.unlink(temp_path)

    def test_empty_directory(self):
        """Should return True for directory with no supported files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory with no supported files
            Path(tmpdir, "test.py").touch()
            
            result = validate_directory(tmpdir)
            assert result is True

    @patch('code.utils.citation_validator.validate_citations')
    def test_all_files_valid(self, mock_validate):
        """Should return True when all files pass validation."""
        mock_validate.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.md").touch()
            Path(tmpdir, "test2.txt").touch()
            
            result = validate_directory(tmpdir)
            assert result is True
            assert mock_validate.call_count == 2

    @patch('code.utils.citation_validator.validate_citations')
    def test_one_file_invalid_non_strict(self, mock_validate):
        """Should return False when one file fails in non-strict mode."""
        mock_validate.side_effect = [True, False, True]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.md").touch()
            Path(tmpdir, "test2.txt").touch()
            Path(tmpdir, "test3.rst").touch()
            
            result = validate_directory(tmpdir, strict_mode=False)
            assert result is False

    @patch('code.utils.citation_validator.validate_citations')
    def test_one_file_invalid_strict(self, mock_validate):
        """Should raise CitationValidationError when one file fails in strict mode."""
        mock_validate.side_effect = [True, False, True]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.md").touch()
            Path(tmpdir, "test2.txt").touch()
            Path(tmpdir, "test3.rst").touch()
            
            with pytest.raises(CitationValidationError):
                validate_directory(tmpdir, strict_mode=True)

    @patch('code.utils.citation_validator.validate_citations')
    def test_custom_extensions(self, mock_validate):
        """Should only validate files with specified extensions."""
        mock_validate.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.md").touch()
            Path(tmpdir, "test.py").touch()
            Path(tmpdir, "test.txt").touch()
            
            # Only validate .py files
            result = validate_directory(tmpdir, extensions=['.py'])
            assert result is True
            mock_validate.assert_called_once()


class TestRunPreCommitHook:
    """Tests for the run_pre_commit_hook function."""

    @patch('code.utils.citation_validator.subprocess.run')
    @patch('code.utils.citation_validator.validate_citations')
    def test_no_staged_files(self, mock_validate, mock_git):
        """Should return 0 when there are no staged files."""
        mock_git.side_effect = FileNotFoundError("Git not found")
        
        result = run_pre_commit_hook()
        assert result == 0
        mock_validate.assert_not_called()

    @patch('code.utils.citation_validator.subprocess.run')
    @patch('code.utils.citation_validator.validate_citations')
    def test_all_files_pass(self, mock_validate, mock_git):
        """Should return 0 when all staged files pass validation."""
        mock_git.return_value = MagicMock(
            returncode=0, 
            stdout="test1.md\ntest2.txt"
        )
        mock_validate.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.md").touch()
            Path(tmpdir, "test2.txt").touch()
            
            # Mock the Path.exists to return True
            with patch('pathlib.Path.exists', return_value=True):
                result = run_pre_commit_hook(
                    staged_files=[
                        Path(tmpdir, "test1.md"),
                        Path(tmpdir, "test2.txt")
                    ]
                )
                assert result == 0

    @patch('code.utils.citation_validator.subprocess.run')
    @patch('code.utils.citation_validator.validate_citations')
    def test_one_file_fails(self, mock_validate, mock_git):
        """Should return 1 when one staged file fails validation."""
        mock_validate.side_effect = [True, False]

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.md").touch()
            Path(tmpdir, "test2.txt").touch()
            
            with patch('pathlib.Path.exists', return_value=True):
                result = run_pre_commit_hook(
                    staged_files=[
                        Path(tmpdir, "test1.md"),
                        Path(tmpdir, "test2.txt")
                    ]
                )
                assert result == 1

    def test_skips_unsupported_extensions(self):
        """Should skip files with unsupported extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.py").touch()
            Path(tmpdir, "test.md").touch()
            
            result = run_pre_commit_hook(
                staged_files=[
                    Path(tmpdir, "test.py"),
                    Path(tmpdir, "test.md")
                ]
            )
            # Should not raise, and should handle gracefully
            assert result == 0