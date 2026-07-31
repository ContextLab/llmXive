import os
import subprocess
import tempfile
import pytest
from pathlib import Path

# Project root relative to test file (assuming tests/unit/ structure)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_ruff_config_exists():
    """Verify that .ruff.toml or pyproject.toml with ruff config exists."""
    ruff_toml = PROJECT_ROOT / ".ruff.toml"
    pyproject = PROJECT_ROOT / "pyproject.toml"
    
    assert ruff_toml.exists() or (
        pyproject.exists() and "[tool.ruff]" in pyproject.read_text()
    ), "Ruff configuration file (.ruff.toml or pyproject.toml) not found."

def test_black_config_exists():
    """Verify that pyproject.toml with black config exists."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found."
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml."

def test_precommit_config_exists():
    """Verify that .pre-commit-config.yaml exists."""
    precommit_config = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert precommit_config.exists(), ".pre-commit-config.yaml not found."

def test_lint_script_exists():
    """Verify that the lint script exists."""
    lint_script = PROJECT_ROOT / "scripts" / "lint.sh"
    assert lint_script.exists(), "scripts/lint.sh not found."

def test_format_script_exists():
    """Verify that the format script exists."""
    format_script = PROJECT_ROOT / "scripts" / "format.sh"
    assert format_script.exists(), "scripts/format.sh not found."

def test_pytest_config_exists():
    """Verify that pytest configuration exists in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found."
    
    content = pyproject.read_text()
    assert "[tool.pytest" in content, "Pytest configuration section not found in pyproject.toml."