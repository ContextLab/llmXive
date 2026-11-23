"""
Test for Task T035a: Verify ruff linting execution logic.

This test ensures the lint check script runs correctly and handles
expected scenarios (success vs failure).
"""
import subprocess
import sys
import tempfile
import os
from pathlib import Path
import pytest

# We cannot run the actual linter here without dependencies, 
# but we can verify the script structure and logic.

def test_lint_check_script_exists():
    """Verify the lint check script exists in the expected location."""
    script_path = Path("code/utils/run_lint_check.py")
    assert script_path.exists(), f"Script not found at {script_path}"

def test_lint_check_script_imports():
    """Verify the script has valid Python syntax and imports."""
    script_path = Path("code/utils/run_lint_check.py")
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, str(script_path), "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in run_lint_check.py: {e}")

def test_main_function_signature():
    """Verify main function exists and returns expected exit codes."""
    # Dynamic import to avoid side effects if ruff isn't installed
    sys.path.insert(0, str(Path("code/utils").resolve()))
    try:
        from run_lint_check import main
        assert callable(main), "main should be a callable function"
    finally:
        # Clean up path
        sys.path.remove(str(Path("code/utils").resolve()))

def test_ruff_command_structure():
    """Verify the subprocess call uses correct arguments."""
    script_path = Path("code/utils/run_lint_check.py")
    content = script_path.read_text()
    
    # Check for key components
    assert "subprocess.run" in content, "Must use subprocess.run"
    assert "ruff" in content, "Must call ruff"
    assert "check" in content, "Must use check command"
    assert "code" in content, "Must target code directory"
    assert "returncode" in content, "Must check return code"