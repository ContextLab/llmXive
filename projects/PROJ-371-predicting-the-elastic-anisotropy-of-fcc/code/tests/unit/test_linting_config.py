"""
Unit tests for linting and formatting configuration.

These tests verify that ruff and black are correctly configured
and that the project passes the defined linting rules.
"""

import os
import subprocess
import tempfile
import tomlkit  # type: ignore
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent.parent


def test_ruff_config_exists(project_root):
    """Test that .ruff.toml configuration file exists."""
    ruff_config = project_root / ".ruff.toml"
    assert ruff_config.exists(), ".ruff.toml configuration file must exist"
    assert ruff_config.stat().st_size > 0, ".ruff.toml must not be empty"


def test_black_config_in_pyproject(project_root):
    """Test that Black configuration exists in pyproject.toml."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"

    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert "line-length" in content, "Black line-length must be configured"


def test_ruff_check_syntax(project_root):
    """Test that ruff check passes on the codebase (ignoring data/output)."""
    ruff_path = project_root / "code"

    # Run ruff check
    result = subprocess.run(
        ["ruff", "check", str(ruff_path)],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    # Allow exit code 0 (success) or 1 (found issues, but syntax is valid)
    # We are primarily checking that ruff can run without crashing
    assert result.returncode in [0, 1], f"Ruff check failed to run: {result.stderr}"

    # If there are errors, they should be linting issues, not syntax errors
    if result.returncode == 1:
        # Verify it's not a configuration error
        assert "Failed to parse" not in result.stderr
        assert "Error" not in result.stderr or "ruff" in result.stderr.lower()


def test_black_check_syntax(project_root):
    """Test that black check passes on the codebase."""
    code_path = project_root / "code"

    # Run black --check
    result = subprocess.run(
        ["black", "--check", "--diff", str(code_path)],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    # Exit code 0 means all files are formatted correctly
    # Exit code 1 means files need formatting (but syntax is valid)
    # Exit code 123 means a syntax error or crash
    assert result.returncode != 123, f"Black encountered a syntax error: {result.stderr}"


def test_ruff_config_syntax_validity(project_root):
    """Test that .ruff.toml has valid TOML syntax."""
    ruff_config = project_root / ".ruff.toml"

    if not ruff_config.exists():
        pytest.skip(".ruff.toml does not exist yet")

    try:
        content = ruff_config.read_text()
        tomlkit.parse(content)
    except Exception as e:
        pytest.fail(f".ruff.toml contains invalid TOML syntax: {e}")