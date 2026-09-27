import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest


class TestLintingConfig:
    """Tests to verify that linting and formatting tools are correctly configured."""

    def test_black_config_exists(self):
        """Verify that a Black configuration exists in the project."""
        # Check for pyproject.toml with [tool.black] section
        pyproject_path = Path("code/pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml must exist for Black config"

        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

    def test_ruff_config_exists(self):
        """Verify that a Ruff configuration exists in the project."""
        # Check for .ruff.toml or ruff section in pyproject.toml
        ruff_toml = Path("code/.ruff.toml")
        pyproject_path = Path("code/pyproject.toml")

        has_ruff_toml = ruff_toml.exists()
        has_ruff_in_pyproject = (
            pyproject_path.exists() and "[tool.ruff]" in pyproject_path.read_text()
        )

        assert has_ruff_toml or has_ruff_in_pyproject, (
            "Must have either .ruff.toml or [tool.ruff] in pyproject.toml"
        )

    def test_makefile_lint_target(self):
        """Verify that Makefile has a lint target."""
        makefile_path = Path("code/Makefile")
        if makefile_path.exists():
            content = makefile_path.read_text()
            assert "lint:" in content, "Makefile must contain 'lint:' target"

    def test_makefile_format_target(self):
        """Verify that Makefile has a format target."""
        makefile_path = Path("code/Makefile")
        if makefile_path.exists():
            content = makefile_path.read_text()
            assert "format:" in content, "Makefile must contain 'format:' target"

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Skipping subprocess tests on Windows"
    )
    def test_ruff_executable_available(self):
        """Verify that ruff can be invoked (if installed)."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, "ruff command should succeed if installed"
        except FileNotFoundError:
            pytest.skip("ruff not installed in environment")
        except subprocess.TimeoutExpired:
            pytest.fail("ruff command timed out")

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Skipping subprocess tests on Windows"
    )
    def test_black_executable_available(self):
        """Verify that black can be invoked (if installed)."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, "black command should succeed if installed"
        except FileNotFoundError:
            pytest.skip("black not installed in environment")
        except subprocess.TimeoutExpired:
            pytest.fail("black command timed out")