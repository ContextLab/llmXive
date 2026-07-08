"""
Contract test for T003: Linting and Formatting Configuration.

Verifies that:
1. ruff and black are installed and runnable.
2. The configuration files exist and are valid TOML.
3. The current codebase (at least this test file) passes the configured linters.
"""
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


def test_ruff_and_black_installed():
    """Verify that ruff and black are available in the environment."""
    try:
        subprocess.run(
            ["ruff", "--version"], check=True, capture_output=True, timeout=10
        )
        subprocess.run(
            ["black", "--version"], check=True, capture_output=True, timeout=10
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.fail(f"Required tools not installed: {e}")


def test_config_files_exist():
    """Verify that configuration files exist in the code directory."""
    code_dir = Path(__file__).parent.parent / "code"
    assert (code_dir / ".ruff.toml").exists(), "Missing .ruff.toml"
    assert (code_dir / ".black.toml").exists(), "Missing .black.toml"
    assert (code_dir / ".pre-commit-config.yaml").exists(), "Missing .pre-commit-config.yaml"


def test_config_files_valid_toml():
    """Verify that TOML config files are syntactically valid."""
    code_dir = Path(__file__).parent.parent / "code"
    ruff_path = code_dir / ".ruff.toml"
    black_path = code_dir / ".black.toml"

    try:
        with open(ruff_path, "rb") as f:
            tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

    try:
        with open(black_path, "rb") as f:
            tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        pytest.fail(f"Invalid TOML in .black.toml: {e}")


def test_ruff_lints_current_code():
    """Run ruff on the current test file to ensure it passes."""
    code_dir = Path(__file__).parent.parent / "code"
    result = subprocess.run(
        [
            "ruff",
            "check",
            str(Path(__file__).absolute()),
            "--config",
            str(code_dir / ".ruff.toml"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # We expect success (exit code 0). If not, print output for debugging.
    if result.returncode != 0:
        pytest.fail(
            f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
        )


def test_black_formatting_current_code():
    """Run black --check on the current test file to ensure it is formatted."""
    code_dir = Path(__file__).parent.parent / "code"
    result = subprocess.run(
        [
            "black",
            "--check",
            "--config",
            str(code_dir / ".black.toml"),
            str(Path(__file__).absolute()),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Black check failed:\n{result.stdout}\n{result.stderr}"
        )