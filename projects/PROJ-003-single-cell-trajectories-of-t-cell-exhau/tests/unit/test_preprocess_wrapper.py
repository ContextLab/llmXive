"""
Unit tests for the preprocess.py wrapper script.

These tests verify:
1. Argument parsing works correctly.
2. R environment checking logic (mocked).
3. Output verification logic.
4. Error handling for missing files/directories.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
# We need to import the functions directly to test them in isolation
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from preprocess import (
    check_r_environment,
    verify_outputs,
    run_r_preprocessing
)

class TestCheckREnvironment:
    """Tests for R environment validation."""

    @patch('subprocess.run')
    def test_r_installed_success(self, mock_run):
        """Test successful R version check."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="R version 4.3.0 (2023-04-21)\nPlatform: x86_64-pc-linux-gnu\n",
            stderr=""
        )
        
        # Mock subsequent checks for Seurat and reticulate
        with patch('subprocess.run') as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = check_r_environment()
            assert result is True

    @patch('subprocess.run')
    def test_r_not_installed(self, mock_run):
        """Test failure when R is not found."""
        mock_run.side_effect = FileNotFoundError("R executable not found")
        
        result = check_r_environment()
        assert result is False

    @patch('subprocess.run')
    def test_seurat_not_installed(self, mock_run):
        """Test failure when Seurat is missing."""
        # First call: R --version (success)
        # Second call: Seurat check (failure)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="R version 4.3.0\n", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="Error: package 'Seurat' not found")
        ]
        
        result = check_r_environment()
        assert result is False


class TestVerifyOutputs:
    """Tests for output file verification."""

    def test_no_outputs_found(self, tmp_path):
        """Test failure when no output files exist."""
        result = verify_outputs(str(tmp_path))
        assert result is False

    def test_empty_file_detected(self, tmp_path):
        """Test failure when output file is empty."""
        empty_file = tmp_path / "test.h5ad"
        empty_file.touch()  # Create empty file
        
        result = verify_outputs(str(tmp_path))
        assert result is False

    def test_valid_outputs_found(self, tmp_path):
        """Test success when valid output files exist."""
        valid_file = tmp_path / "processed.h5ad"
        valid_file.write_text("dummy content")  # Non-empty file
        
        result = verify_outputs(str(tmp_path))
        assert result is True

    def test_multiple_output_types(self, tmp_path):
        """Test verification with multiple output files."""
        (tmp_path / "cell1.h5ad").write_text("data1")
        (tmp_path / "cell2.h5ad").write_text("data2")
        (tmp_path / "metadata.txt").write_text("text")  # Should be ignored
        
        result = verify_outputs(str(tmp_path))
        assert result is True


class TestRunRPreprocessing:
    """Tests for R script execution."""

    def test_input_directory_missing(self, tmp_path):
        """Test failure when input directory does not exist."""
        fake_input = str(tmp_path / "nonexistent")
        fake_output = str(tmp_path / "output")
        fake_script = str(tmp_path / "script.R")
        
        result = run_r_preprocessing(fake_input, fake_output, fake_script)
        assert result is False

    def test_r_script_missing(self, tmp_path):
        """Test failure when R script does not exist."""
        fake_input = str(tmp_path)
        fake_output = str(tmp_path / "output")
        fake_script = str(tmp_path / "nonexistent.R")
        
        # Create input dir
        Path(fake_input).mkdir(exist_ok=True)
        
        result = run_r_preprocessing(fake_input, fake_output, fake_script)
        assert result is False

    @patch('subprocess.run')
    def test_r_script_success(self, mock_run, tmp_path):
        """Test successful R script execution."""
        fake_input = str(tmp_path)
        fake_output = str(tmp_path / "output")
        fake_script = str(tmp_path / "script.R")
        
        # Setup directories and file
        Path(fake_input).mkdir(exist_ok=True)
        Path(fake_output).mkdir(exist_ok=True)
        Path(fake_script).touch()
        
        mock_run.return_value = MagicMock(returncode=0)
        
        result = run_r_preprocessing(fake_input, fake_output, fake_script)
        assert result is True
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'Rscript' in call_args
        assert fake_script in call_args

    @patch('subprocess.run')
    def test_r_script_failure(self, mock_run, tmp_path):
        """Test failure when R script returns non-zero."""
        fake_input = str(tmp_path)
        fake_output = str(tmp_path / "output")
        fake_script = str(tmp_path / "script.R")
        
        Path(fake_input).mkdir(exist_ok=True)
        Path(fake_script).touch()
        
        mock_run.return_value = MagicMock(returncode=1, stderr="Error in R script")
        
        result = run_r_preprocessing(fake_input, fake_output, fake_script)
        assert result is False
