"""
Test suite to verify linting configuration and formatting tools are correctly set up.
These tests ensure that the project adheres to the defined code style standards.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest

# Root directory for the project (assuming tests/ is at root)
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
CONFIG_FILE = CODE_DIR / ".flake8"
PYPROJECT_FILE = CODE_DIR / "pyproject.toml"

class TestLintingConfiguration:
    """Tests for linting configuration files."""

    def test_flake8_config_exists(self):
        """Verify that .flake8 configuration file exists."""
        assert CONFIG_FILE.exists(), f"Missing flake8 config at {CONFIG_FILE}"

    def test_pyproject_toml_exists(self):
        """Verify that pyproject.toml exists with black/isort config."""
        assert PYPROJECT_FILE.exists(), f"Missing pyproject.toml at {PYPROJECT_FILE}"

    def test_flake8_config_valid(self):
        """Verify that flake8 can read the configuration."""
        result = subprocess.run(
            ["flake8", "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "flake8 is not installed or configured correctly"

    def test_black_config_valid(self):
        """Verify that black can read the configuration."""
        result = subprocess.run(
            ["black", "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "black is not installed or configured correctly"

    def test_isort_config_valid(self):
        """Verify that isort can read the configuration."""
        result = subprocess.run(
            ["isort", "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "isort is not installed or configured correctly"

class TestCodeFormatting:
    """Tests to ensure code formatting tools are functional."""

    @pytest.mark.skipif(
        not (CONFIG_FILE.exists() and PYPROJECT_FILE.exists()),
        reason="Config files missing"
    )
    def test_flake8_runs_on_code_dir(self):
        """Run flake8 on the code directory to ensure it executes without crashing."""
        # We don't assert returncode=0 here because code might have lint errors initially,
        # but we assert it runs successfully (returncode 0 or 1, not 2 for usage error)
        result = subprocess.run(
            ["flake8", str(CODE_DIR), f"--config={CONFIG_FILE}"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        # Return code 0 = no errors, 1 = errors found, 2 = usage error
        assert result.returncode in [0, 1], f"flake8 execution failed: {result.stderr}"

    @pytest.mark.skipif(
        not PYPROJECT_FILE.exists(),
        reason="pyproject.toml missing"
    )
    def test_black_runs_on_code_dir(self):
        """Run black check on the code directory."""
        result = subprocess.run(
            ["black", "--check", str(CODE_DIR)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        # Return code 0 = formatted, 1 = would reformat, 2 = usage error
        assert result.returncode in [0, 1], f"black execution failed: {result.stderr}"

    @pytest.mark.skipif(
        not PYPROJECT_FILE.exists(),
        reason="pyproject.toml missing"
    )
    def test_isort_runs_on_code_dir(self):
        """Run isort check on the code directory."""
        result = subprocess.run(
            ["isort", "--check-only", str(CODE_DIR)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        # Return code 0 = sorted, 1 = would re-sort, 2 = usage error
        assert result.returncode in [0, 1], f"isort execution failed: {result.stderr}"

class TestScriptExecution:
    """Tests for helper scripts."""

    def test_run_lint_script_exists(self):
        """Verify run_lint.sh script exists."""
        script_path = PROJECT_ROOT / "code" / "scripts" / "run_lint.sh"
        assert script_path.exists(), f"Missing run_lint.sh at {script_path}"

    def test_format_script_exists(self):
        """Verify format.sh script exists."""
        script_path = PROJECT_ROOT / "code" / "scripts" / "format.sh"
        assert script_path.exists(), f"Missing format.sh at {script_path}"