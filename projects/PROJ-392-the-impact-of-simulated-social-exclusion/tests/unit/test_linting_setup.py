"""
Unit tests for linting setup and runner utilities.
"""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.lint_runner import run_flake8, run_black, run_isort, run_all_checks, format_all


class TestLintRunner:
    """Test cases for lint runner utilities."""

    def test_run_flake8_returns_tuple(self):
        """Test that run_flake8 returns a tuple of (int, str)."""
        # We mock the subprocess to avoid actually running flake8
        with patch("utils.lint_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            code, output = run_flake8(["code"])
            assert isinstance(code, int)
            assert isinstance(output, str)
            assert code == 0

    def test_run_black_returns_tuple(self):
        """Test that run_black returns a tuple of (int, str)."""
        with patch("utils.lint_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            code, output = run_black(["code"])
            assert isinstance(code, int)
            assert isinstance(output, str)
            assert code == 0

    def test_run_isort_returns_tuple(self):
        """Test that run_isort returns a tuple of (int, str)."""
        with patch("utils.lint_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            code, output = run_isort(["code"])
            assert isinstance(code, int)
            assert isinstance(output, str)
            assert code == 0

    def test_run_flake8_file_not_found(self):
        """Test that run_flake8 handles missing flake8 installation."""
        with patch("utils.lint_runner.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("flake8 not found")
            code, output = run_flake8()
            assert code == 1
            assert "flake8 is not installed" in output

    def test_run_black_file_not_found(self):
        """Test that run_black handles missing black installation."""
        with patch("utils.lint_runner.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("black not found")
            code, output = run_black()
            assert code == 1
            assert "black is not installed" in output

    def test_run_isort_file_not_found(self):
        """Test that run_isort handles missing isort installation."""
        with patch("utils.lint_runner.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("isort not found")
            code, output = run_isort()
            assert code == 1
            assert "isort is not installed" in output

    def test_run_all_checks_success(self):
        """Test run_all_checks when all tools pass."""
        with patch("utils.lint_runner.run_flake8") as mock_flake8, \
             patch("utils.lint_runner.run_isort") as mock_isort, \
             patch("utils.lint_runner.run_black") as mock_black:
            
            mock_flake8.return_value = (0, "")
            mock_isort.return_value = (0, "")
            mock_black.return_value = (0, "")
            
            result = run_all_checks()
            assert result is True
            mock_flake8.assert_called_once()
            mock_isort.assert_called_once()
            mock_black.assert_called_once()

    def test_run_all_checks_failure(self):
        """Test run_all_checks when one tool fails."""
        with patch("utils.lint_runner.run_flake8") as mock_flake8, \
             patch("utils.lint_runner.run_isort") as mock_isort, \
             patch("utils.lint_runner.run_black") as mock_black:
            
            mock_flake8.return_value = (1, "Error in code")
            mock_isort.return_value = (0, "")
            mock_black.return_value = (0, "")
            
            result = run_all_checks()
            assert result is False
            mock_flake8.assert_called_once()
            # isort and black should not be called after flake8 fails
            mock_isort.assert_not_called()
            mock_black.assert_not_called()

    def test_format_all_success(self):
        """Test format_all when all tools succeed."""
        with patch("utils.lint_runner.run_isort") as mock_isort, \
             patch("utils.lint_runner.run_black") as mock_black:
            
            mock_isort.return_value = (0, "")
            mock_black.return_value = (0, "")
            
            result = format_all()
            assert result is True
            mock_isort.assert_called_once()
            mock_black.assert_called_once()

    def test_format_all_failure(self):
        """Test format_all when one tool fails."""
        with patch("utils.lint_runner.run_isort") as mock_isort, \
             patch("utils.lint_runner.run_black") as mock_black:
            
            mock_isort.return_value = (1, "Error in isort")
            mock_black.return_value = (0, "")
            
            result = format_all()
            assert result is False
            mock_isort.assert_called_once()
            # black should not be called after isort fails
            mock_black.assert_not_called()