"""
Tests to verify that linting and formatting tools are properly configured.
"""
import subprocess
import sys
from pathlib import Path

import pytest


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists with Black and Ruff configuration."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml must exist"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration must be in pyproject.toml"
    assert "[tool.ruff]" in content, "Ruff configuration must be in pyproject.toml"
    assert "line-length" in content, "line-length must be configured"


def test_ruff_config_exists():
    """Test that .ruff.toml or ruff configuration exists."""
    project_root = get_project_root()
    ruff_toml = project_root / ".ruff.toml"
    pyproject_toml = project_root / "pyproject.toml"

    # Either a dedicated .ruff.toml or config in pyproject.toml is acceptable
    has_ruff_toml = ruff_toml.exists()
    has_ruff_in_pyproject = pyproject_toml.exists() and "[tool.ruff]" in pyproject_toml.read_text()

    assert has_ruff_toml or has_ruff_in_pyproject, "Ruff configuration must exist"


def test_black_config_exists():
    """Test that Black configuration exists."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml must exist"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration must be present"


def test_lint_tool_exists():
    """Test that the lint tool script exists."""
    project_root = get_project_root()
    lint_tool = project_root / "code" / "tools" / "lint.py"

    assert lint_tool.exists(), "Lint tool (code/tools/lint.py) must exist"

    # Check that it has the required imports and functions
    content = lint_tool.read_text()
    assert "import subprocess" in content, "Lint tool must import subprocess"
    assert "def run_command" in content, "Lint tool must have run_command function"
    assert "def main" in content, "Lint tool must have main function"


def test_format_tool_exists():
    """Test that the format tool script exists."""
    project_root = get_project_root()
    format_tool = project_root / "code" / "tools" / "format.py"

    assert format_tool.exists(), "Format tool (code/tools/format.py) must exist"

    # Check that it has the required imports and functions
    content = format_tool.read_text()
    assert "import subprocess" in content, "Format tool must import subprocess"
    assert "def run_command" in content, "Format tool must have run_command function"
    assert "def main" in content, "Format tool must have main function"


def test_ruff_is_installable():
    """Test that ruff is available in the environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.skip("Ruff not installed in environment")


def test_black_is_installable():
    """Test that black is available in the environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.skip("Black not installed in environment")