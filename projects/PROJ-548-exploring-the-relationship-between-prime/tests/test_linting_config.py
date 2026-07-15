"""
Test to verify that linting and formatting configurations are valid.
This ensures the project setup for T003 is functional.
"""
import os
import subprocess
import sys
from pathlib import Path

def test_ruff_config_exists():
    """Verify ruff.toml exists in the code directory."""
    code_dir = Path(__file__).parent.parent / "code"
    config_path = code_dir / "ruff.toml"
    assert config_path.exists(), f"ruff.toml not found at {config_path}"

def test_black_config_exists():
    """Verify .black.toml exists in the code directory."""
    code_dir = Path(__file__).parent.parent / "code"
    config_path = code_dir / ".black.toml"
    assert config_path.exists(), f".black.toml not found at {config_path}"

def test_requirements_dev_includes_linters():
    """Verify requirements-dev.txt includes ruff and black."""
    root_dir = Path(__file__).parent.parent
    req_path = root_dir / "code" / "requirements-dev.txt"
    assert req_path.exists(), "requirements-dev.txt not found"
    
    content = req_path.read_text()
    assert "ruff" in content.lower(), "ruff not found in requirements-dev.txt"
    assert "black" in content.lower(), "black not found in requirements-dev.txt"

def test_script_executables_exist():
    """Verify helper scripts exist."""
    scripts_dir = Path(__file__).parent.parent / "code" / "scripts"
    assert (scripts_dir / "format.sh").exists(), "format.sh not found"
    assert (scripts_dir / "lint.sh").exists(), "lint.sh not found"
    assert (scripts_dir / "format_check.sh").exists(), "format_check.sh not found"
    assert (scripts_dir / "lint_check.sh").exists(), "lint_check.sh not found"

def test_ruff_syntax_check_on_dummy_file(tmp_path):
    """Verify ruff can parse a dummy file without crashing."""
    # Create a temporary valid python file
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("x = 1\n")
    
    # Run ruff check on it
    result = subprocess.run(
        ["ruff", "check", str(dummy_file)],
        capture_output=True,
        text=True
    )
    # Should exit with 0 (no errors) or 1 (linting errors found)
    # but should not crash (exit code > 1 usually indicates internal error)
    assert result.returncode in (0, 1), f"Ruff crashed: {result.stderr}"