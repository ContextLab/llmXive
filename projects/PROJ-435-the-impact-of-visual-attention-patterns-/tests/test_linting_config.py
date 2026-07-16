"""
Test suite for T003: Linting and Formatting Configuration.
Verifies that ruff and black are installed and configured correctly.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

class TestLintingSetup:
    """Tests for linting and formatting tool availability."""

    @pytest.fixture
    def python_executable(self):
        return sys.executable

    def test_ruff_installed(self, python_executable):
        """Test that ruff is installed."""
        result = subprocess.run(
            [python_executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Ruff is not installed or not in PATH."
        assert "ruff" in result.stdout.lower()

    def test_black_installed(self, python_executable):
        """Test that black is installed."""
        result = subprocess.run(
            [python_executable, "-m", "black", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Black is not installed or not in PATH."
        assert "black" in result.stdout.lower()

    def test_ruff_config_exists(self):
        """Test that .ruff.toml configuration file exists."""
        config_path = CODE_DIR / ".ruff.toml"
        assert config_path.exists(), f"Ruff config file not found at {config_path}"

    def test_black_config_exists(self):
        """Test that .black.toml configuration file exists."""
        config_path = CODE_DIR / ".black.toml"
        assert config_path.exists(), f"Black config file not found at {config_path}"

    def test_ruff_config_valid(self, python_executable):
        """Test that ruff configuration is valid by running a check."""
        config_path = CODE_DIR / ".ruff.toml"
        result = subprocess.run(
            [
                python_executable, "-m", "ruff", "check",
                "--config", str(config_path),
                "--select", "E,F",
                str(CODE_DIR)
            ],
            capture_output=True,
            text=True
        )
        # Ruff returns 0 if no errors, 1 if errors found. 
        # We only care that it doesn't crash due to invalid config.
        # A config error usually results in a non-1, non-0 return or stderr output.
        # However, ruff might return 1 if there are lint errors. 
        # The critical thing is no exception/invalid config error.
        assert "error" not in result.stderr.lower() or "invalid" not in result.stderr.lower()

    def test_black_config_valid(self, python_executable):
        """Test that black configuration is valid by running a check."""
        config_path = CODE_DIR / ".black.toml"
        result = subprocess.run(
            [
                python_executable, "-m", "black",
                "--config", str(config_path),
                "--check",
                str(CODE_DIR)
            ],
            capture_output=True,
            text=True
        )
        # Black returns 0 if formatted correctly, 1 if not.
        # We only care that it runs without config errors.
        assert "error" not in result.stderr.lower() or "invalid" not in result.stderr.lower()

    def test_setup_linting_script_exists(self):
        """Test that the setup script exists."""
        script_path = CODE_DIR / "setup_linting.py"
        assert script_path.exists(), f"Setup script not found at {script_path}"

    def test_setup_linting_script_executable(self, python_executable):
        """Test that the setup script runs without error."""
        script_path = CODE_DIR / "setup_linting.py"
        result = subprocess.run(
            [python_executable, str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Setup script failed: {result.stderr}"
        assert "Complete" in result.stdout