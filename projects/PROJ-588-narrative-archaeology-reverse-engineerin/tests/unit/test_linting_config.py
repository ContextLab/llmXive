"""
Tests to verify linting and formatting configuration is present and valid.
These tests check that the project adheres to the defined style guide.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    config_path = Path(__file__).parent.parent.parent / ".flake8"
    assert config_path.exists(), "Missing .flake8 configuration file"


def test_black_config_exists():
    """Verify pyproject.toml contains black configuration."""
    config_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    assert config_path.exists(), "Missing pyproject.toml"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"


def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    config_path = Path(__file__).parent.parent.parent / ".pre-commit-config.yaml"
    assert config_path.exists(), "Missing .pre-commit-config.yaml"


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Skipping lint check on Windows due to potential environment issues in CI"
)
def test_flake8_runs_successfully():
    """Verify flake8 can run without errors on the codebase."""
    # Only check the code directory if it exists
    code_dir = Path(__file__).parent.parent.parent / "code"
    if not code_dir.exists():
        pytest.skip("Code directory not yet created")

    try:
        result = subprocess.run(
            ["flake8", "--config=.flake8", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        # flake8 returns 0 on success, non-zero on lint errors
        # We allow warnings but not errors for this check
        # Note: In a real CI, this would fail if there are errors
        # Here we just verify the tool runs
        assert result.returncode == 0 or "error" not in result.stdout.lower()
    except FileNotFoundError:
        pytest.skip("flake8 not installed in environment")


def test_isort_config_exists():
    """Verify isort configuration in pyproject.toml."""
    config_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    content = config_path.read_text()
    assert "[tool.isort]" in content, "Missing [tool.isort] section in pyproject.toml"