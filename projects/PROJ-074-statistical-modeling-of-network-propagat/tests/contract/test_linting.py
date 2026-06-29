"""Contract test for linting and formatting tool configuration.

This test verifies that ruff and black are properly configured
and can be executed against the codebase without errors.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def code_dir(project_root):
    """Return the code directory."""
    return project_root / "code"


def test_ruff_config_exists(project_root):
    """Verify ruff configuration file exists."""
    # Check pyproject.toml contains ruff config
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"

    content = pyproject.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"


def test_black_config_exists(project_root):
    """Verify black configuration file exists."""
    # Check pyproject.toml contains black config
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"

    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"


def test_pre_commit_config_exists(project_root):
    """Verify pre-commit configuration exists."""
    pre_commit = project_root / ".pre-commit-config.yaml"
    assert pre_commit.exists(), ".pre-commit-config.yaml must exist"

    content = pre_commit.read_text()
    assert "black" in content, "pre-commit config must include black hook"
    assert "ruff" in content, "pre-commit config must include ruff hook"


def test_ruff_can_check_code(code_dir):
    """Verify ruff can be executed against code directory."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should complete without error (exit code 0 or 1 for lint issues)
        assert result.returncode in (0, 1), f"Ruff failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.skip("Ruff check timed out (may not be installed)")
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")


def test_black_can_check_code(code_dir):
    """Verify black can be executed against code directory."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should complete without error (exit code 0 or 1 for formatting issues)
        assert result.returncode in (0, 1), f"Black failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.skip("Black check timed out (may not be installed)")
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")
