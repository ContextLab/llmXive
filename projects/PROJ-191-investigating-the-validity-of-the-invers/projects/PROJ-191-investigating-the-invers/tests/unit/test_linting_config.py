"""
Unit tests to verify that linting and formatting configurations are present and valid.
"""
import os
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # Navigate up from tests/unit to project root
    return current_file.parent.parent.parent


def test_pyproject_toml_exists(project_root):
    """Test that pyproject.toml exists in the project root."""
    config_path = project_root / "pyproject.toml"
    assert config_path.exists(), f"pyproject.toml not found at {config_path}"


def test_black_config_present(project_root):
    """Test that black configuration exists in pyproject.toml."""
    config_path = project_root / "pyproject.toml"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Black configuration not found in pyproject.toml"
    assert "line-length" in content, "Black line-length not configured"
    assert "target-version" in content, "Black target-version not configured"


def test_ruff_config_present(project_root):
    """Test that ruff configuration exists in pyproject.toml."""
    config_path = project_root / "pyproject.toml"
    content = config_path.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration not found in pyproject.toml"
    assert "line-length" in content, "Ruff line-length not configured"
    assert "select" in content, "Ruff select rules not configured"


def test_precommit_config_exists(project_root):
    """Test that .pre-commit-config.yaml exists."""
    config_path = project_root / ".pre-commit-config.yaml"
    assert config_path.exists(), ".pre-commit-config.yaml not found"


def test_precommit_has_black(project_root):
    """Test that pre-commit config includes black hook."""
    config_path = project_root / ".pre-commit-config.yaml"
    content = config_path.read_text()
    assert "black" in content, "Black hook not found in .pre-commit-config.yaml"


def test_precommit_has_ruff(project_root):
    """Test that pre-commit config includes ruff hook."""
    config_path = project_root / ".pre-commit-config.yaml"
    content = config_path.read_text()
    assert "ruff" in content, "Ruff hook not found in .pre-commit-config.yaml"


def test_format_tool_exists(project_root):
    """Test that the format tool script exists."""
    tool_path = project_root / "code" / "tools" / "format.py"
    assert tool_path.exists(), "code/tools/format.py not found"


def test_lint_tool_exists(project_root):
    """Test that the lint tool script exists."""
    tool_path = project_root / "code" / "tools" / "lint.py"
    assert tool_path.exists(), "code/tools/lint.py not found"
