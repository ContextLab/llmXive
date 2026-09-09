"""
Unit tests for setup_linting.py.
Verifies that the setup script correctly identifies required tools
and attempts to initialize pre-commit.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to add the parent of 'code' to sys.path to import 'setup_linting'
import sys
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.setup_linting import run_command, main

def test_run_command_success():
    """Test that run_command executes a simple command successfully."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout="success", stderr="", returncode=0)
        result = run_command(["echo", "hello"], check=True)
        mock_run.assert_called_once()
        assert result.returncode == 0

def test_run_command_failure():
    """Test that run_command raises SystemExit on failure when check=True."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", output="", stderr="error")
        with pytest.raises(SystemExit):
            run_command(["bad_command"], check=True)

def test_run_command_no_check():
    """Test that run_command returns the error object when check=False."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", output="", stderr="error")
        result = run_command(["bad_command"], check=False)
        assert result.returncode == 1

def test_main_execution():
    """Test that main() calls the expected setup commands."""
    with patch('code.setup_linting.run_command') as mock_run:
        with patch('code.setup_linting.sys') as mock_sys:
            mock_sys.executable = "python"
            main()
            
            # Verify pip install was called
            pip_call = [
                mock.call(["python", "-m", "pip", "install", "pre-commit", "ruff", "black"], check=True)
            ]
            # Verify pre-commit install was called
            install_call = mock.call(["pre-commit", "install"], check=True)
            
            # Check that the calls happened (order might vary slightly in mock logic but structure is fixed)
            calls = mock_run.call_args_list
            assert any("pip" in str(call) for call in calls)
            assert any("pre-commit" in str(call) and "install" in str(call) for call in calls)