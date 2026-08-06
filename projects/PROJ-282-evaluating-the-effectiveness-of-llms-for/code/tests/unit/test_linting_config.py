"""
Tests to verify that linting and formatting configurations are correctly set up.
"""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    # Assuming the tests are run from the repository root or code root
    # We look for pyproject.toml to determine the root
    current = Path(__file__).resolve()
    # If running from code/tests/unit, go up 3 to get to code/
    root = current.parent.parent.parent.parent
    # If running from code/ (where tests are), go up 2
    if not (root / "pyproject.toml").exists():
        root = current.parent.parent
    return root


def test_ruff_config_exists(project_root):
    """Verify that .ruff.toml or ruff section in pyproject.toml exists."""
    ruff_toml = project_root / ".ruff.toml"
    pyproject = project_root / "pyproject.toml"
    assert ruff_toml.exists() or (
        pyproject.exists() and "ruff" in pyproject.read_text()
    ), "Ruff configuration file not found."


def test_black_config_exists(project_root):
    """Verify that black section in pyproject.toml exists."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found."
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration not found in pyproject.toml."


def test_precommit_config_exists(project_root):
    """Verify that .pre-commit-config.yaml exists."""
    config = project_root / ".pre-commit-config.yaml"
    assert config.exists(), "Pre-commit configuration file not found."


def test_lint_script_exists(project_root):
    """Verify that the setup_linting script exists."""
    script = project_root / "code" / "scripts" / "setup_linting.py"
    # Adjust path based on where the script is actually located
    # Based on task, it's at code/code/scripts/setup_linting.py
    script_correct = project_root / "code" / "code" / "scripts" / "setup_linting.py"
    assert script_correct.exists(), "Setup linting script not found."


def test_format_script_exists(project_root):
    """Verify that formatting can be called (ruff/black present)."""
    # We check if the commands are available, not the script itself
    try:
        subprocess.run(
            ["ruff", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            ["black", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        pytest.skip("Linting tools not installed in environment.")


def test_pytest_config_exists(project_root):
    """Verify that pytest configuration exists in pyproject.toml."""
    pyproject = project_root / "pyproject.toml"
    content = pyproject.read_text()
    assert "[tool.pytest" in content, "Pytest configuration not found in pyproject.toml."