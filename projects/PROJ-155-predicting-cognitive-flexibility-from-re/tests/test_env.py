"""
Environment verification tests for T001.
Checks directory structure and linting compliance.
"""
import subprocess
from pathlib import Path
from llmxive_toolkit import paths

def test_directories_exist():
    """Verify that all required project directories are present."""
    required_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
        paths.docs(),
        paths.path("tests"),
    ]
    for d in required_dirs:
        assert d.is_dir(), f"Required directory missing: {d}"

def test_linting_passes():
    """Verify that the codebase passes ruff linting."""
    # Run ruff check on the project root
    result = subprocess.run(
        ["ruff", "check", "."], 
        capture_output=True, 
        text=True
    )
    assert result.returncode == 0, (
        f"Ruff linting failed with return code {result.returncode}:\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )