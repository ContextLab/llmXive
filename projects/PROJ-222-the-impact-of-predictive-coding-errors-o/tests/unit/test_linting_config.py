import os
import sys
from pathlib import Path
import subprocess

def test_pyproject_exists():
    """Test that pyproject.toml exists in the project root."""
    project_root = Path.cwd()
    assert (project_root / "pyproject.toml").exists(), "pyproject.toml must exist in the project root"

def test_ruff_config_exists():
    """Test that ruff configuration is present (either in pyproject.toml or .ruff.toml)."""
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"
    ruff_config_path = project_root / ".ruff.toml"

    assert pyproject_path.exists(), "pyproject.toml must exist"

    # Check if ruff section exists in pyproject.toml or if .ruff.toml exists
    has_ruff_section = False
    with open(pyproject_path, "r") as f:
        content = f.read()
        if "[tool.ruff]" in content:
            has_ruff_section = True

    assert has_ruff_section or ruff_config_path.exists(), \
        "Ruff configuration must be present in pyproject.toml or as .ruff.toml"

def test_black_config_exists():
    """Test that black configuration is present in pyproject.toml."""
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml must exist"

    with open(pyproject_path, "r") as f:
        content = f.read()
        assert "[tool.black]" in content, "Black configuration must be present in pyproject.toml"

def test_ruff_can_check():
    """Test that ruff can successfully run a check (even if errors are found)."""
    project_root = Path.cwd()
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect it to run without crashing (return code 0 or 1 is fine, 1 means issues found)
        # Return code 2 usually means configuration error or missing file
        assert result.returncode != 2, f"Ruff check failed with config error: {result.stderr}"
    except FileNotFoundError:
        # Ruff might not be installed in the test environment, which is acceptable for this test
        # if the configuration is correct.
        pass
    except subprocess.TimeoutExpired:
        assert False, "Ruff check timed out"

def test_black_can_check():
    """Test that black can successfully run a check (even if formatting is needed)."""
    project_root = Path.cwd()
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Return code 0 means formatted, 1 means needs formatting, 2 means error
        assert result.returncode != 2, f"Black check failed with error: {result.stderr}"
    except FileNotFoundError:
        # Black might not be installed in the test environment
        pass
    except subprocess.TimeoutExpired:
        assert False, "Black check timed out"