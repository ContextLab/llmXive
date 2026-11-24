"""Unit test for T003b: pyproject.toml Black configuration."""

import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


def load_pyproject() -> dict:
    assert PYPROJECT.exists(), f"Missing {PYPROJECT}"
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)


def test_black_line_length_is_100():
    config = load_pyproject()
    assert config["tool"]["black"]["line-length"] == 100


def test_black_target_version_is_py311():
    config = load_pyproject()
    assert "py311" in config["tool"]["black"]["target-version"]


def test_black_check_code_dir():
    """`black --check code/` must exit 0 (files are Black-formatted)."""
    import subprocess

    result = subprocess.run(
        ["black", "--check", "code/"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"black --check code/ failed (rc={result.returncode}):\n{result.stdout}\n{result.stderr}"
    )