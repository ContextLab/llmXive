"""
Unit tests for linting configuration module.
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest

from linting_config import run_flake8_check, run_black_check, run_black_format, run_all_checks


class TestRunFlake8Check:
    def test_flake8_passes(self):
        """Test that run_flake8_check returns True when flake8 passes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            assert run_flake8_check() is True

    def test_flake8_fails(self):
        """Test that run_flake8_check returns False when flake8 fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="Some errors", stderr="Some warnings"
            )
            assert run_flake8_check() is False

    def test_flake8_exception(self):
        """Test that run_flake8_check returns False when an exception occurs."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Test error")
            assert run_flake8_check() is False


class TestRunBlackCheck:
    def test_black_passes(self):
        """Test that run_black_check returns True when black passes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            assert run_black_check() is True

    def test_black_fails(self):
        """Test that run_black_check returns False when black fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="Would reformat", stderr=""
            )
            assert run_black_check() is False

    def test_black_exception(self):
        """Test that run_black_check returns False when an exception occurs."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Test error")
            assert run_black_check() is False


class TestRunBlackFormat:
    def test_black_format_success(self):
        """Test that run_black_format returns True when formatting succeeds."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            assert run_black_format() is True

    def test_black_format_failure(self):
        """Test that run_black_format returns False when formatting fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="Error", stderr="Error"
            )
            assert run_black_format() is False

    def test_black_format_exception(self):
        """Test that run_black_format returns False when an exception occurs."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Test error")
            assert run_black_format() is False


class TestRunAllChecks:
    def test_all_checks_pass(self):
        """Test that run_all_checks returns True when all checks pass."""
        with patch("linting_config.run_flake8_check") as mock_flake8, patch(
            "linting_config.run_black_check"
        ) as mock_black:
            mock_flake8.return_value = True
            mock_black.return_value = True
            assert run_all_checks() is True

    def test_flake8_fails(self):
        """Test that run_all_checks returns False when flake8 fails."""
        with patch("linting_config.run_flake8_check") as mock_flake8, patch(
            "linting_config.run_black_check"
        ) as mock_black:
            mock_flake8.return_value = False
            mock_black.return_value = True
            assert run_all_checks() is False

    def test_black_fails(self):
        """Test that run_all_checks returns False when black fails."""
        with patch("linting_config.run_flake8_check") as mock_flake8, patch(
            "linting_config.run_black_check"
        ) as mock_black:
            mock_flake8.return_value = True
            mock_black.return_value = False
            assert run_all_checks() is False

    def test_both_fail(self):
        """Test that run_all_checks returns False when both checks fail."""
        with patch("linting_config.run_flake8_check") as mock_flake8, patch(
            "linting_config.run_black_check"
        ) as mock_black:
            mock_flake8.return_value = False
            mock_black.return_value = False
            assert run_all_checks() is False
