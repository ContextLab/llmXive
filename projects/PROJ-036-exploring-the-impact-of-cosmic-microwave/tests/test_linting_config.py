"""
Tests to verify that linting and formatting configuration files exist and are valid.
"""
import os
import toml
from pathlib import Path

import pytest

# Determine the project root relative to this test file
# Assuming tests/ is at root level or code/tests/
# Based on tasks.md: "Single project: `src/`, `tests/` at repository root"
# But T001 created `code/`, `data/`...
# Let's assume tests are in `code/tests/` or `tests/` at root.
# We will look for the pyproject.toml or ruff.toml in parent directories.

def find_project_root(start_path: Path) -> Path:
    """Find the project root by looking for specific markers."""
    current = start_path
    while current != current.parent:
        if (current / "ruff.toml").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return start_path

@pytest.fixture
def project_root():
    return find_project_root(Path(__file__).parent)

def test_ruff_config_exists(project_root):
    """Assert that ruff.toml exists in the project root."""
    ruff_path = project_root / "ruff.toml"
    assert ruff_path.exists(), f"ruff.toml not found at {ruff_path}"

def test_ruff_config_valid(project_root):
    """Assert that ruff.toml is valid TOML (ruff supports TOML)."""
    ruff_path = project_root / "ruff.toml"
    try:
        # Ruff uses TOML format
        with open(ruff_path, "r", encoding="utf-8") as f:
            toml.load(f)
        assert True
    except Exception as e:
        pytest.fail(f"ruff.toml is not valid TOML: {e}")

def test_black_config_in_pyproject(project_root):
    """Assert that pyproject.toml exists and contains black configuration."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"
    
    content = pyproject_path.read_text(encoding="utf-8")
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"

def test_requirements_contains_linting_tools(project_root):
    """Assert that requirements.txt contains ruff and black."""
    req_path = project_root / "requirements.txt"
    if not req_path.exists():
        # If requirements.txt doesn't exist, the setup task might have failed or
        # the project uses a different dependency management.
        # However, T002 initialized requirements.txt.
        pytest.fail("requirements.txt not found")
    
    content = req_path.read_text(encoding="utf-8").lower()
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"