import os
import subprocess
import tempfile
import pytest
from pathlib import Path

def test_ruff_config_exists():
    """Verify that ruff configuration exists."""
    root = Path(__file__).resolve().parent.parent.parent
    # Check pyproject.toml or .ruff.toml
    pyproject = root / "pyproject.toml"
    ruff_toml = root / ".ruff.toml"
    assert pyproject.exists() or ruff_toml.exists(), "Ruff config (pyproject.toml or .ruff.toml) missing"

def test_black_config_exists():
    """Verify that black configuration exists."""
    root = Path(__file__).resolve().parent.parent.parent
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "Black config (pyproject.toml) missing"
    with open(pyproject, "r") as f:
        content = f.read()
    assert "[tool.black]" in content, "Black section missing in pyproject.toml"

def test_precommit_config_exists():
    """Verify that pre-commit configuration exists."""
    root = Path(__file__).resolve().parent.parent.parent
    config = root / ".pre-commit-config.yaml"
    assert config.exists(), ".pre-commit-config.yaml missing"

def test_lint_script_exists():
    """Verify that setup_linting.py exists."""
    root = Path(__file__).resolve().parent.parent.parent
    script = root / "scripts" / "setup_linting.py"
    assert script.exists(), "scripts/setup_linting.py missing"

def test_format_script_exists():
    """Verify that format scripts exist or are handled by pre-commit."""
    # Pre-commit handles formatting via ruff-format/black
    root = Path(__file__).resolve().parent.parent.parent
    config = root / ".pre-commit-config.yaml"
    assert config.exists(), ".pre-commit-config.yaml missing"
    with open(config, "r") as f:
        content = f.read()
    assert "ruff" in content or "black" in content, "No formatting hook found in pre-commit config"

def test_pytest_config_exists():
    """Verify that pytest configuration exists."""
    root = Path(__file__).resolve().parent.parent.parent
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml missing"
    with open(pyproject, "r") as f:
        content = f.read()
    assert "[tool.pytest" in content, "Pytest config section missing in pyproject.toml"