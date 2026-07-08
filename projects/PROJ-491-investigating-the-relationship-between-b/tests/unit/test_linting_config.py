"""
Unit tests for linting and formatting configuration utilities.
"""

import subprocess
import sys
from unittest.mock import patch, MagicMock
from code.linting_config import run_flake8, run_black, run_isort, main


def test_run_flake8_success():
    """Test that run_flake8 returns 0 when no issues are found."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_flake8("code", max_line_length=88)

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "flake8" in call_args
        assert "--max-line-length=88" in call_args


def test_run_flake8_failure():
    """Test that run_flake8 returns non-zero when issues are found."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = run_flake8("code")

        assert result == 1


def test_run_black_check_mode():
    """Test that run_black includes --check when check_only=True."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_black("code", check_only=True)

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "--check" in call_args


def test_run_black_format_mode():
    """Test that run_black does not include --check when check_only=False."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_black("code", check_only=False)

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "--check" not in call_args


def test_run_isort_check_mode():
    """Test that run_isort includes --check-only when check_only=True."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_isort("code", check_only=True)

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "--check-only" in call_args


def test_run_isort_format_mode():
    """Test that run_isort does not include --check-only when check_only=False."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_isort("code", check_only=False)

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "--check-only" not in call_args


def test_main_with_check_flag():
    """Test main function with --check flag."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch('sys.argv', ['main', '--check']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once()
                assert mock_exit.call_args[0][0] == 0


def test_main_with_fix_flag():
    """Test main function with --fix flag."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch('sys.argv', ['main', '--fix']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once()
                assert mock_exit.call_args[0][0] == 0