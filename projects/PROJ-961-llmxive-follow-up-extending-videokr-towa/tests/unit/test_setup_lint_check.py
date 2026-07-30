import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_lint_check import run_ruff_check, main
from utils.config import get_project_root

def test_run_ruff_check_creates_log():
    """Test that run_ruff_check creates the log file."""
    # We mock the subprocess call to simulate a successful run
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch("setup_lint_check.subprocess.run", return_value=mock_result):
        # Ensure the log directory exists
        project_root = get_project_root()
        log_path = project_root / "data" / "processed" / "lint_log.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = run_ruff_check()
        
        # Check that the function returned True
        assert success is True
        
        # Check that the log file was created
        assert log_path.exists(), f"Log file {log_path} was not created"
        
        # Check that the log file has content
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Ruff Check Log" in content
            assert "Exit Code: 0" in content

def test_run_ruff_check_fails_on_nonzero_exit():
    """Test that run_ruff_check returns False when ruff fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "F811 redefinition of unused 'foo'"
    mock_result.stderr = ""
    
    with patch("setup_lint_check.subprocess.run", return_value=mock_result):
        project_root = get_project_root()
        log_path = project_root / "data" / "processed" / "lint_log.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = run_ruff_check()
        
        assert success is False
        assert log_path.exists()

def test_run_ruff_check_handles_missing_ruff():
    """Test that run_ruff_check handles FileNotFoundError when ruff is missing."""
    with patch("setup_lint_check.subprocess.run", side_effect=FileNotFoundError("ruff not found")):
        project_root = get_project_root()
        log_path = project_root / "data" / "processed" / "lint_log.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = run_ruff_check()
        
        assert success is False
        assert log_path.exists()
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "ruff not found" in content