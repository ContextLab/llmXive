"""
Tests to verify that linting and formatting configurations are valid
and that the project structure adheres to the configured rules.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RUFF_CONFIG = PROJECT_ROOT / "code" / ".ruff.toml"
PYPROJECT_CONFIG = PROJECT_ROOT / "code" / "pyproject.toml"
REQUIREMENTS = PROJECT_ROOT / "code" / "requirements.txt"


def test_config_files_exist():
    """Verify that linting/formatting config files exist."""
    assert RUFF_CONFIG.exists(), "ruff config (.ruff.toml) missing"
    assert PYPROJECT_CONFIG.exists(), "pyproject.toml missing"
    assert REQUIREMENTS.exists(), "requirements.txt missing"


def test_requirements_include_linting_tools():
    """Verify that ruff and black are in requirements.txt."""
    content = REQUIREMENTS.read_text()
    assert "ruff" in content.lower(), "ruff not found in requirements.txt"
    assert "black" in content.lower(), "black not found in requirements.txt"


@pytest.mark.skipif(
    not subprocess.run(["which", "ruff"], capture_output=True).returncode == 0,
    reason="ruff not installed in environment",
)
def test_ruff_syntax_check():
    """Run ruff check to ensure no syntax errors or style violations in code/.
    
    This test ensures the configuration is valid and the codebase (if any)
    passes the linting rules defined in .ruff.toml.
    """
    result = subprocess.run(
        ["ruff", "check", str(CODE_DIR)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    # ruff returns 0 if no issues found, non-zero otherwise.
    # We accept 0 as success. If there are issues, the test fails,
    # prompting the developer to fix them.
    assert result.returncode == 0, (
        f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    )


@pytest.mark.skipif(
    not subprocess.run(["which", "black"], capture_output=True).returncode == 0,
    reason="black not installed in environment",
)
def test_black_format_check():
    """Run black --check to ensure code is formatted correctly.
    
    This test ensures the codebase adheres to the formatting rules.
    """
    result = subprocess.run(
        ["black", "--check", str(CODE_DIR)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, (
        f"Black format check failed:\n{result.stdout}\n{result.stderr}"
    )
