"""
Tests to verify that linting and formatting configurations are present and valid.
These tests ensure that the project adheres to the specified code style.
"""
import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists in the project root."""
    assert PYPROJECT_PATH.exists(), "pyproject.toml must exist in the project root."

def test_pyproject_toml_contains_black_config():
    """Verify that pyproject.toml contains Black configuration."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.black]" in content, "Black configuration section [tool.black] must be present in pyproject.toml."
    assert "line-length = 88" in content, "Black line-length must be set to 88."
    assert "target-version = ['py311']" in content, "Black target-version must include py311."

def test_pyproject_toml_contains_isort_config():
    """Verify that pyproject.toml contains isort configuration."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.isort]" in content, "isort configuration section [tool.isort] must be present in pyproject.toml."
    assert "profile = \"black\"" in content, "isort profile must be set to black."

def test_pyproject_toml_contains_ruff_config():
    """Verify that pyproject.toml contains Ruff configuration."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration section [tool.ruff] must be present in pyproject.toml."
    assert "line-length = 88" in content, "Ruff line-length must be set to 88."
    assert "target-version = \"py311\"" in content, "Ruff target-version must be py311."

def test_pyproject_toml_contains_pytest_config():
    """Verify that pyproject.toml contains pytest configuration."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.pytest.ini_options]" in content, "pytest configuration section [tool.pytest.ini_options] must be present in pyproject.toml."
    assert "testpaths = [\"tests\"]" in content, "pytest testpaths must be set to tests."

def test_gitignore_exists():
    """Verify that .gitignore exists in the project root."""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist in the project root."

def test_gitignore_contains_data_patterns():
    """Verify that .gitignore contains patterns for data directories."""
    content = (PROJECT_ROOT / ".gitignore").read_text()
    assert "data/raw/*" in content, ".gitignore must exclude data/raw/*."
    assert "data/processed/*" in content, ".gitignore must exclude data/processed/*."
    assert "!data/raw/.gitkeep" in content, ".gitignore must keep .gitkeep in data/raw."
    assert "!data/processed/.gitkeep" in content, ".gitignore must keep .gitkeep in data/processed."

@pytest.mark.skipif(
    not (PROJECT_ROOT / ".ruff.toml").exists() and not PYPROJECT_PATH.exists(),
    reason="Ruff is not configured in this project."
)
def test_ruff_check_passes():
    """Run ruff check to ensure code style compliance."""
    try:
        result = subprocess.run(
            ["ruff", "check", "code"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # Ruff returns 0 on success, 1 on failure.
        # We expect this to pass if the code is compliant.
        assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff is not installed in the environment.")

@pytest.mark.skipif(
    not (PROJECT_ROOT / "pyproject.toml").exists(),
    reason="Black is not configured in this project."
)
def test_black_check_passes():
    """Run black --check to ensure code formatting compliance."""
    try:
        result = subprocess.run(
            ["black", "--check", "code"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # Black returns 0 on success, 1 on failure.
        assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black is not installed in the environment.")

@pytest.mark.skipif(
    not (PROJECT_ROOT / "pyproject.toml").exists(),
    reason="isort is not configured in this project."
)
def test_isort_check_passes():
    """Run isort --check to ensure import sorting compliance."""
    try:
        result = subprocess.run(
            ["isort", "--check", "code"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # isort returns 0 on success, 1 on failure.
        assert result.returncode == 0, f"isort check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("isort is not installed in the environment.")