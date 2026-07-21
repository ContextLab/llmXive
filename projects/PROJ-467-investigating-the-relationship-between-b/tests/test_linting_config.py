import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    return Path(__file__).parent.parent


def test_pyproject_toml_exists(project_root):
    """Test that pyproject.toml exists in the project root."""
    assert (project_root / "pyproject.toml").exists()


def test_pyproject_toml_contains_black_config(project_root):
    """Test that pyproject.toml contains Black configuration."""
    pyproject_path = project_root / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content
    assert "line-length" in content
    assert "target-version" in content


def test_pyproject_toml_contains_isort_config(project_root):
    """Test that pyproject.toml contains isort configuration."""
    pyproject_path = project_root / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.isort]" in content
    assert "profile" in content
    assert "line_length" in content


def test_pyproject_toml_contains_ruff_config(project_root):
    """Test that pyproject.toml contains Ruff configuration."""
    pyproject_path = project_root / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content
    assert "line-length" in content
    assert "select" in content


def test_pyproject_toml_contains_pytest_config(project_root):
    """Test that pyproject.toml contains pytest configuration."""
    pyproject_path = project_root / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.pytest.ini_options]" in content
    assert "testpaths" in content


def test_gitignore_exists(project_root):
    """Test that .gitignore exists in the project root."""
    assert (project_root / ".gitignore").exists()


def test_gitignore_contains_data_patterns(project_root):
    """Test that .gitignore contains data artifact patterns."""
    gitignore_path = project_root / ".gitignore"
    content = gitignore_path.read_text()
    assert "data/" in content
    assert "*.nii" in content
    assert "*.csv" in content
    assert "results/" in content


def test_ruff_check_passes(project_root):
    """Test that ruff check passes on the codebase."""
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed")
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")


def test_black_check_passes(project_root):
    """Test that black check passes on the codebase."""
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed")
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")


def test_isort_check_passes(project_root):
    """Test that isort check passes on the codebase."""
    try:
        result = subprocess.run(
            ["isort", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Isort check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("Isort not installed")
    except subprocess.TimeoutExpired:
        pytest.fail("Isort check timed out")