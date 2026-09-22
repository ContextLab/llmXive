"""
Unit tests for the linting configuration module.

These tests verify that the linting_config module correctly identifies
tool availability and executes commands (mocked where necessary).
"""

import subprocess
from unittest.mock import patch, MagicMock
import pytest

# Import the module to test
from code import linting_config


class TestVerifyToolsInstalled:
    def test_both_installed(self):
        """Test when both ruff and black are installed."""
        with patch("subprocess.run") as mock_run:
            # Mock successful runs for both
            mock_run.side_effect = [
                MagicMock(returncode=0), # ruff
                MagicMock(returncode=0), # black
            ]
            ruff_ok, black_ok = linting_config.verify_tools_installed()
            assert ruff_ok is True
            assert black_ok is True

    def test_ruff_missing(self):
        """Test when ruff is missing."""
        with patch("subprocess.run") as mock_run:
            # Mock failure for ruff, success for black
            mock_run.side_effect = [
                FileNotFoundError("ruff not found"),
                MagicMock(returncode=0), # black
            ]
            ruff_ok, black_ok = linting_config.verify_tools_installed()
            assert ruff_ok is False
            assert black_ok is True

    def test_black_missing(self):
        """Test when black is missing."""
        with patch("subprocess.run") as mock_run:
            # Mock success for ruff, failure for black
            mock_run.side_effect = [
                MagicMock(returncode=0), # ruff
                FileNotFoundError("black not found"),
            ]
            ruff_ok, black_ok = linting_config.verify_tools_installed()
            assert ruff_ok is True
            assert black_ok is False

    def test_both_missing(self):
        """Test when both are missing."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                FileNotFoundError("ruff not found"),
                FileNotFoundError("black not found"),
            ]
            ruff_ok, black_ok = linting_config.verify_tools_installed()
            assert ruff_ok is False
            assert black_ok is False


class TestRunRuffCheck:
    def test_check_passes(self):
        """Test successful ruff check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = linting_config.run_ruff_check()
            assert result is True
            mock_run.assert_called_once_with(
                ["ruff", "check", "code/", "tests/"],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_check_fails(self):
        """Test failed ruff check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="E501 Line too long\n"
            )
            # CalledProcessError is raised by check=True on non-zero return
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["ruff", "check", "code/", "tests/"]
            )
            result = linting_config.run_ruff_check()
            assert result is False


class TestRunBlackCheck:
    def test_check_passes(self):
        """Test successful black check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = linting_config.run_black_check()
            assert result is True
            mock_run.assert_called_once_with(
                ["black", "--check", "code/", "tests/"],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_check_fails(self):
        """Test failed black check."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["black", "--check", "code/", "tests/"]
            )
            result = linting_config.run_black_check()
            assert result is False
