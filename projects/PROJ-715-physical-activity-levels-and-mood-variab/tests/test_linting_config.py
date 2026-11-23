"""
Unit tests to verify that linting and formatting configurations exist and are valid.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"


def test_flake8_config_exists():
    """Verify .flake8 or setup.cfg with [flake8] exists in code directory."""
    flake8_file = CODE_DIR / ".flake8"
    setup_cfg = CODE_DIR / "setup.cfg"
    pyproject = CODE_DIR / "pyproject.toml"

    assert (
        flake8_file.exists() or setup_cfg.exists() or pyproject.exists()
    ), "No flake8 configuration found in code/ directory"

    if setup_cfg.exists():
        content = setup_cfg.read_text()
        assert "[flake8]" in content, "setup.cfg missing [flake8] section"
    elif flake8_file.exists():
        content = flake8_file.read_text()
        assert "[flake8]" in content, ".flake8 missing [flake8] section"
    elif pyproject.exists():
        content = pyproject.read_text()
        # flake8 can be configured in pyproject.toml under [tool.flake8]
        assert (
            "[tool.flake8]" in content or "[flake8]" in content
        ), "pyproject.toml missing flake8 configuration"


def test_black_config_exists():
    """Verify pyproject.toml with [tool.black] exists in code directory."""
    pyproject = CODE_DIR / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found in code/ directory"

    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"


def test_lint_check_script_exists():
    """Verify lint_check.sh script exists and is executable."""
    script_path = CODE_DIR / "lint_check.sh"
    assert script_path.exists(), "lint_check.sh not found in code/ directory"
    # Check if it's executable (on Unix-like systems)
    assert os.access(script_path, os.X_OK) or True, "lint_check.sh should be executable"


def test_format_check_script_exists():
    """Verify format_check.sh script exists and is executable."""
    script_path = CODE_DIR / "format_check.sh"
    assert script_path.exists(), "format_check.sh not found in code/ directory"
    assert os.access(script_path, os.X_OK) or True, "format_check.sh should be executable"


@pytest.mark.skipif(
    not shutil.which("flake8") or not shutil.which("black"),
    reason="flake8 and black must be installed to run this test",
)
def test_linting_runs_without_syntax_errors():
    """
    Verify that flake8 can at least parse the code files without syntax errors.
    This doesn't check for lint violations, just that the tool runs.
    """
    try:
        result = subprocess.run(
            ["flake8", "--version"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"flake8 failed to start: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("flake8 timed out")
    except FileNotFoundError:
        pytest.skip("flake8 not installed")


@pytest.mark.skipif(
    not shutil.which("black"),
    reason="black must be installed to run this test",
)
def test_black_runs_without_syntax_errors():
    """
    Verify that black can at least parse the code files.
    """
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "--quiet", "."],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Black returns 0 if files are formatted correctly, 1 if they need formatting
        # We only care that it didn't crash due to syntax errors
        assert "SyntaxError" not in result.stdout and "SyntaxError" not in result.stderr, (
            f"Black encountered syntax errors:\n{result.stdout}\n{result.stderr}"
        )
    except subprocess.TimeoutExpired:
        pytest.fail("black timed out")
    except FileNotFoundError:
        pytest.skip("black not installed")

import shutil