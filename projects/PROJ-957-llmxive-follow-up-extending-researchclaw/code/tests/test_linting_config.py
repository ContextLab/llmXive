import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def test_ruff_config_exists(project_root):
    """Verify that ruff configuration exists in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist"

    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
    assert 'line-length = 88' in content, "Ruff must have line-length = 88"
    assert 'target-version = "py311"' in content, "Ruff must target Python 3.11"


def test_black_config_exists(project_root):
    """Verify that black configuration exists in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert 'line-length = 88' in content, "Black must have line-length = 88"
    assert 'target-version = ["py311"]' in content, "Black must target Python 3.11"


def test_pyproject_dev_dependencies(project_root):
    """Verify that dev dependencies include ruff and black."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist"

    content = pyproject_path.read_text()
    # Check for optional dev dependencies section or direct dependencies
    assert "ruff" in content.lower(), "pyproject.toml should reference ruff"
    assert "black" in content.lower(), "pyproject.toml should reference black"


def test_ruff_check_syntax(project_root, tmp_path):
    """Run ruff check on a temporary valid Python file to ensure tool works."""
    # Create a temporary valid Python file
    test_file = tmp_path / "test_syntax.py"
    test_file.write_text("x = 1\nprint(x)\n")

    # Run ruff check
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(test_file)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # Ruff should exit with 0 if no issues found
    assert result.returncode == 0, f"Ruff check failed: {result.stderr}"


def test_black_check_syntax(project_root, tmp_path):
    """Run black --check on a temporary valid Python file to ensure tool works."""
    # Create a temporary valid Python file
    test_file = tmp_path / "test_syntax.py"
    test_file.write_text("x = 1\nprint(x)\n")

    # Run black check
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(test_file)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # Black should exit with 0 if file is already formatted
    assert result.returncode == 0, f"Black check failed: {result.stderr}"
