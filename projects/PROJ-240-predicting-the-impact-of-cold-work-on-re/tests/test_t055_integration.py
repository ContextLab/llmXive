"""
Integration test for T055: Reconcile run-book vs implementation.
Verifies that code/main.py exists and can invoke the pipeline steps
without raising FileNotFoundError.
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_main_script_exists():
    """Verify code/main.py exists."""
    main_path = CODE_DIR / "main.py"
    assert main_path.exists(), f"code/main.py does not exist. Path: {main_path}"

def test_main_script_syntax():
    """Verify code/main.py is syntactically valid Python."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(CODE_DIR / "main.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Syntax error in code/main.py: {result.stderr}"

def test_main_help_command():
    """Verify main.py responds to --help."""
    result = subprocess.run(
        [sys.executable, "code/main.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Failed to run help: {result.stderr}"
    assert "--step" in result.stdout

def test_main_generate_step_exists_in_args():
    """Verify 'generate' is a valid step."""
    result = subprocess.run(
        [sys.executable, "code/main.py", "--step", "generate"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # The step might fail due to missing data, but it should not fail with "unrecognized arguments"
    # or "No such file or directory" for the script itself.
    assert "unrecognized arguments" not in result.stderr
    assert "No such file or directory" not in result.stderr