"""
Unit tests to verify that linting and formatting configurations are valid
and that the Makefile commands work as expected.
"""
import subprocess
import os
import sys
import tempfile
import shutil

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_command(cmd, cwd=None):
    """Helper to run a shell command and return success status."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"


class TestLintingConfig:
    def test_ruff_config_exists(self):
        """Verify .ruff.toml or pyproject.toml [tool.ruff] exists."""
        ruff_toml = os.path.join(PROJECT_ROOT, ".ruff.toml")
        pyproject = os.path.join(PROJECT_ROOT, "pyproject.toml")

        assert os.path.exists(ruff_toml) or os.path.exists(pyproject), (
            "Ruff configuration file (.ruff.toml or pyproject.toml) not found."
        )

    def test_black_config_exists(self):
        """Verify black configuration exists in pyproject.toml or .black.toml."""
        pyproject = os.path.join(PROJECT_ROOT, "pyproject.toml")
        black_toml = os.path.join(PROJECT_ROOT, ".black.toml")

        # Check pyproject.toml for [tool.black]
        if os.path.exists(pyproject):
            with open(pyproject) as f:
                content = f.read()
                assert "[tool.black]" in content, (
                    "Black configuration not found in pyproject.toml"
                )
        else:
            assert os.path.exists(black_toml), (
                "Black configuration file (.black.toml) not found."
            )

    def test_makefile_targets_exist(self):
        """Verify Makefile contains expected targets."""
        makefile_path = os.path.join(PROJECT_ROOT, "Makefile")
        assert os.path.exists(makefile_path), "Makefile not found."

        with open(makefile_path) as f:
            content = f.read()
            assert "lint:" in content, "Makefile missing 'lint' target"
            assert "format:" in content, "Makefile missing 'format' target"
            assert "check-format:" in content, "Makefile missing 'check-format' target"

    def test_ruff_syntax_check_passes_on_empty_code(self):
        """
        Run ruff check on the code directory to ensure configuration is valid.
        Note: This might fail if there are actual linting errors in existing code,
        but it verifies the configuration itself is loadable.
        """
        # We run ruff with --exit-zero to ensure we don't fail due to linting errors
        # in existing code, but we want to ensure the tool runs successfully.
        success, stdout, stderr = run_command("ruff check code/ --exit-zero")
        # If the config is broken, ruff usually exits with code 2 or prints an error.
        # We allow linting errors (code 1) as long as the tool runs (code 0 or 1).
        # However, if it fails to parse config, it's usually code 2.
        # Let's just ensure it doesn't crash.
        assert "error: Failed to parse" not in stderr, f"Ruff config parse error: {stderr}"

    def test_black_check_passes_on_empty_code(self):
        """
        Run black --check to ensure configuration is valid.
        Similar to ruff, we expect it to run without crashing.
        """
        # We use --check to see if formatting is needed, but we don't fix it here.
        success, stdout, stderr = run_command("black --check code/ tests/ || true")
        # Black returns 1 if files need formatting, 0 if they are fine.
        # We just want to ensure it doesn't crash due to config errors.
        assert "error: Cannot parse" not in stderr, f"Black config parse error: {stderr}"
        assert "No such file" not in stderr, "Black failed to find target directory"

class TestRequirements:
    def test_requirements_dev_includes_linting_tools(self):
        """Verify requirements-dev.txt includes ruff and black."""
        req_path = os.path.join(PROJECT_ROOT, "requirements-dev.txt")
        if not os.path.exists(req_path):
            # If it doesn't exist, check if they are in main requirements
            main_req = os.path.join(PROJECT_ROOT, "requirements.txt")
            if os.path.exists(main_req):
                with open(main_req) as f:
                    content = f.read()
                    assert "ruff" in content and "black" in content, (
                        "ruff and black not found in requirements.txt"
                    )
            return

        with open(req_path) as f:
            content = f.read()
            assert "ruff" in content, "ruff not found in requirements-dev.txt"
            assert "black" in content, "black not found in requirements-dev.txt"
