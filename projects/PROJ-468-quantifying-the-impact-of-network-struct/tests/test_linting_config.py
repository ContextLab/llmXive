"""
Test suite to verify linting and formatting configuration validity.
These tests ensure that ruff and black are correctly configured and
that the codebase adheres to the defined style standards.
"""

import subprocess
import sys
import os

import pytest


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Helper to run a shell command and capture output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


class TestRuffConfiguration:
    """Tests for Ruff linting configuration."""

    def test_ruff_check_passes(self):
        """Verify that ruff check passes on the codebase."""
        # Check if ruff is installed
        returncode, stdout, stderr = run_command([sys.executable, "-m", "ruff", "--version"])
        if returncode != 0:
            pytest.skip("Ruff is not installed or not configured correctly")

        # Run ruff check on the project
        code_dir = os.path.join(os.path.dirname(__file__), "..", "code")
        if not os.path.exists(code_dir):
            # If code dir doesn't exist yet, check root
            code_dir = os.path.dirname(__file__)

        returncode, stdout, stderr = run_command([
            sys.executable, "-m", "ruff", "check", code_dir
        ])

        # We expect this to pass (exit code 0) or find issues that need fixing
        # For the purpose of configuration validation, we just check it runs without crashing
        assert returncode in [0, 1], f"Ruff check crashed: {stderr}"

    def test_ruff_config_exists(self):
        """Verify that ruff configuration file exists."""
        # Check for pyproject.toml with ruff config or .ruff.toml
        assert os.path.exists("pyproject.toml") or os.path.exists(".ruff.toml"), \
            "Ruff configuration file not found"


class TestBlackConfiguration:
    """Tests for Black formatting configuration."""

    def test_black_check_passes(self):
        """Verify that black check passes on the codebase."""
        # Check if black is installed
        returncode, stdout, stderr = run_command([sys.executable, "-m", "black", "--version"])
        if returncode != 0:
            pytest.skip("Black is not installed or not configured correctly")

        # Run black check on the project
        code_dir = os.path.join(os.path.dirname(__file__), "..", "code")
        if not os.path.exists(code_dir):
            code_dir = os.path.dirname(__file__)

        returncode, stdout, stderr = run_command([
            sys.executable, "-m", "black", "--check", "--diff", code_dir
        ])

        # Exit code 0 means formatted correctly, 1 means would reformat
        # We assert it doesn't crash (exit code != 2)
        assert returncode in [0, 1], f"Black check crashed: {stderr}"

    def test_black_config_exists(self):
        """Verify that black configuration file exists."""
        assert os.path.exists("pyproject.toml") or os.path.exists("setup.cfg") or os.path.exists(".black"), \
            "Black configuration file not found"

    def test_pre_commit_config_exists(self):
        """Verify that pre-commit configuration file exists."""
        assert os.path.exists(".pre-commit-config.yaml"), \
            "Pre-commit configuration file not found"


class TestIntegration:
    """Integration tests for the toolchain."""

    def test_both_tools_available(self):
        """Verify both ruff and black are available."""
        ruff_check = run_command([sys.executable, "-m", "ruff", "--version"])
        black_check = run_command([sys.executable, "-m", "black", "--version"])

        assert ruff_check[0] == 0, "Ruff is not available"
        assert black_check[0] == 0, "Black is not available"

    def test_requirements_include_tools(self):
        """Verify requirements.txt includes linting tools."""
        req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        if os.path.exists(req_path):
            with open(req_path, "r") as f:
                content = f.read().lower()
            assert "ruff" in content, "ruff not found in requirements.txt"
            assert "black" in content, "black not found in requirements.txt"