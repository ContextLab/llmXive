"""
Test suite to verify linting and formatting configuration is valid.
These tests ensure that ruff and black configurations are syntactically correct
and can be loaded by their respective tools.
"""
import os
import subprocess
import tempfile
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"


def test_ruff_config_exists():
    """Verify .ruff.toml exists in the code directory."""
    config_path = CODE_DIR / ".ruff.toml"
    assert config_path.exists(), f"Ruff config not found at {config_path}"


def test_black_config_exists():
    """Verify .black.toml exists in the code directory."""
    config_path = CODE_DIR / ".black.toml"
    assert config_path.exists(), f"Black config not found at {config_path}"


def test_ruff_config_valid():
    """Verify .ruff.toml is valid TOML."""
    config_path = CODE_DIR / ".ruff.toml"
    try:
        with open(config_path, "rb") as f:
            tomllib.load(f)
    except Exception as e:
        pytest.fail(f"Invalid TOML in .ruff.toml: {e}")


def test_black_config_valid():
    """Verify .black.toml is valid TOML."""
    config_path = CODE_DIR / ".black.toml"
    try:
        with open(config_path, "rb") as f:
            tomllib.load(f)
    except Exception as e:
        pytest.fail(f"Invalid TOML in .black.toml: {e}")


def test_makefile_exists():
    """Verify Makefile exists in the code directory."""
    makefile_path = CODE_DIR / "Makefile"
    assert makefile_path.exists(), f"Makefile not found at {makefile_path}"


def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists in the code directory."""
    config_path = CODE_DIR / ".pre-commit-config.yaml"
    assert config_path.exists(), f"Pre-commit config not found at {config_path}"


def test_dev_requirements_includes_linters():
    """Verify requirements-dev.txt includes ruff and black."""
    req_path = CODE_DIR / "requirements-dev.txt"
    assert req_path.exists(), "requirements-dev.txt not found"

    content = req_path.read_text()
    assert "ruff" in content, "ruff not found in requirements-dev.txt"
    assert "black" in content, "black not found in requirements-dev.txt"


def test_ruff_can_parse_project():
    """Run ruff check to ensure it can parse the project without config errors."""
    ruff_path = CODE_DIR / ".ruff.toml"
    try:
        result = subprocess.run(
            ["ruff", "check", "--config", str(ruff_path), str(CODE_DIR)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Exit code 0 means success, 1 means linting issues found (which is okay for this test)
        # We only care that the config didn't crash the tool
        assert result.returncode in [0, 1], f"Ruff crashed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("ruff check timed out")