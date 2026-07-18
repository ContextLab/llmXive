"""
Tests to verify that linting and formatting configuration is valid and
that the project structure adheres to the defined standards.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_black_config_exists():
    """Verify pyproject.toml contains black configuration."""
    pyproject = CODE_DIR / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist in code/"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert "line-length = 88" in content, "Black line-length must be 88"

def test_flake8_config_exists():
    """Verify .flake8 configuration exists and is valid."""
    flake8_cfg = CODE_DIR / ".flake8"
    assert flake8_cfg.exists(), ".flake8 must exist in code/"
    content = flake8_cfg.read_text()
    assert "[flake8]" in content, ".flake8 must contain [flake8] section"
    assert "max-line-length = 88" in content, "Flake8 max-line-length must be 88"

def test_dev_requirements_includes_tools():
    """Verify requirements-dev.txt includes black and flake8."""
    req_file = CODE_DIR / "requirements-dev.txt"
    assert req_file.exists(), "requirements-dev.txt must exist in code/"
    content = req_file.read_text()
    assert "black" in content, "requirements-dev.txt must include black"
    assert "flake8" in content, "requirements-dev.txt must include flake8"

def test_run_flake8_on_empty_code_dir():
    """
    Run flake8 on the code directory.
    Note: This test assumes the code directory might be empty or have
    minimal files at this stage. We expect it to pass if no python files
    are present or if they conform to the config.
    """
    flake8_path = CODE_DIR / ".flake8"
    if not flake8_path.exists():
        pytest.skip(".flake8 config not found, skipping lint check")

    # Run flake8 on the code directory
    # We use a subprocess to ensure the config file is picked up correctly
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(CODE_DIR)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        # If there are no python files, flake8 might exit with 0 and no output
        # If there are files, they must pass.
        # We assert that the exit code is 0 (success)
        assert result.returncode == 0, f"Flake8 found issues:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("flake8 not installed in environment, skipping lint check")
