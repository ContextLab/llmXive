"""
Contract test for Task T038: Code cleanup and refactoring.

This test verifies that the cleanup script exists and can be imported.
It does not run the full black/flake8 suite here to avoid dependency on 
external binary execution in the test runner, but ensures the logic is present.
"""
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

def test_cleanup_script_exists(project_root):
    """Assert that the cleanup script exists."""
    script_path = project_root / "code" / "cleanup_and_format.py"
    assert script_path.exists(), f"Cleanup script not found at {script_path}"

def test_cleanup_script_syntax(project_root):
    """Assert that the cleanup script is syntactically valid Python."""
    script_path = project_root / "code" / "cleanup_and_format.py"
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            compile(f.read(), script_path, "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in cleanup script: {e}")

def test_cleanup_script_executes(project_root):
    """
    Assert that the cleanup script runs without crashing.
    We run it with --help or just execute it. Since it runs black/flake8,
    we expect it to complete (even if linting fails, the script should handle it).
    """
    script_path = project_root / "code" / "cleanup_and_format.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    # The script should exit 0 even if flake8 finds issues, 
    # as per the logic in the script (it prints a warning but exits 0).
    # If it crashes (e.g. missing imports), exit code will be non-zero.
    assert result.returncode == 0, f"Cleanup script crashed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
