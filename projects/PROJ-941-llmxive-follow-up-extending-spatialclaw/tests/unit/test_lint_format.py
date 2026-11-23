"""
Tests for the lint_format utility script.
These tests verify that the script exists and has the expected interface.
Actual linting behavior is verified by running the script manually or via CI.
"""
import subprocess
import sys
import os
import pytest

@pytest.fixture
def project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_lint_format_script_exists(project_root):
    """Verify that the lint_format.py script exists."""
    script_path = os.path.join(project_root, "code", "tools", "lint_format.py")
    assert os.path.exists(script_path), f"Script not found at {script_path}"

def test_lint_format_help(project_root):
    """Verify that the script responds to --help."""
    script_path = os.path.join(project_root, "code", "tools", "lint_format.py")
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        assert "linting" in result.stdout.lower() or "formatting" in result.stdout.lower()
    except FileNotFoundError:
        pytest.skip("subprocess not available in this environment")

def test_ruff_config_exists(project_root):
    """Verify that ruff configuration exists."""
    pyproject = os.path.join(project_root, "pyproject.toml")
    ruff_toml = os.path.join(project_root, ".ruff.toml")
    
    assert os.path.exists(pyproject) or os.path.exists(ruff_toml), \
        "Either pyproject.toml or .ruff.toml must exist"
    
    if os.path.exists(pyproject):
        with open(pyproject, "r") as f:
            content = f.read()
            assert "[tool.ruff" in content, "Ruff configuration not found in pyproject.toml"
            assert "line-length" in content, "line-length not configured for ruff"

def test_black_config_exists(project_root):
    """Verify that black configuration exists."""
    pyproject = os.path.join(project_root, "pyproject.toml")
    
    if os.path.exists(pyproject):
        with open(pyproject, "r") as f:
            content = f.read()
            assert "[tool.black" in content, "Black configuration not found in pyproject.toml"
            assert "line-length" in content, "line-length not configured for black"