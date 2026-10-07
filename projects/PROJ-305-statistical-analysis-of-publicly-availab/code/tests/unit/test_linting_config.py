import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

class TestLintingConfig:
    """Tests to verify linting and formatting configuration files exist and are valid."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).resolve().parent.parent.parent

    def test_pyproject_toml_exists(self, project_root):
        """Verify pyproject.toml exists."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in project root"

    def test_pyproject_toml_valid(self, project_root):
        """Verify pyproject.toml contains valid TOML and required sections."""
        pyproject_path = project_root / "pyproject.toml"
        try:
            import tomllib
        except ImportError:
            # Fallback for Python < 3.11
            import tomli as tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        assert "project" in data, "pyproject.toml must contain [project] section"
        assert "tool" in data, "pyproject.toml must contain [tool] section"
        assert "black" in data["tool"], "pyproject.toml must contain [tool.black] section"
        assert "ruff" in data["tool"], "pyproject.toml must contain [tool.ruff] section"

    def test_flake8_config_exists(self, project_root):
        """Verify .flake8 configuration file exists."""
        flake8_path = project_root / ".flake8"
        assert flake8_path.exists(), ".flake8 must exist in project root"

    def test_flake8_config_valid(self, project_root):
        """Verify .flake8 contains valid configuration."""
        flake8_path = project_root / ".flake8"
        content = flake8_path.read_text()
        assert "[flake8]" in content, ".flake8 must contain [flake8] section"
        assert "max-line-length" in content, ".flake8 must define max-line-length"

    def test_ruff_config_exists(self, project_root):
        """Verify .ruff.toml or [tool.ruff] in pyproject.toml exists."""
        ruff_toml = project_root / ".ruff.toml"
        pyproject = project_root / "pyproject.toml"

        assert (
            ruff_toml.exists() or self._has_ruff_section(pyproject)
        ), "Ruff configuration must exist (.ruff.toml or [tool.ruff] in pyproject.toml)"

    def _has_ruff_section(self, pyproject_path):
        """Helper to check if pyproject.toml has [tool.ruff] section."""
        if not pyproject_path.exists():
            return False
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        return "ruff" in data.get("tool", {})

    def test_black_config_exists(self, project_root):
        """Verify Black configuration exists in pyproject.toml."""
        pyproject_path = project_root / "pyproject.toml"
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        assert "black" in data.get("tool", {}), "Black configuration must exist in pyproject.toml"

    def test_ruff_check_runs(self, project_root):
        """Verify ruff can run against the project without crashing."""
        ruff_path = project_root / "code"
        if not ruff_path.exists():
            pytest.skip("code directory not found, skipping ruff check")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "--diff", str(ruff_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # ruff returns 0 if no errors, 1 if errors found, 2 if config error
            # We just want to ensure it runs without crashing (exit code != 2 usually)
            # or if it finds linting errors, that's fine too.
            # The key is it doesn't crash with a syntax error in config.
            assert result.returncode != 2, f"Ruff configuration error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("ruff not installed in environment, skipping execution test")
        except subprocess.TimeoutExpired:
            pytest.skip("ruff check timed out")

    def test_black_check_runs(self, project_root):
        """Verify black can run against the project without crashing."""
        code_path = project_root / "code"
        if not code_path.exists():
            pytest.skip("code directory not found, skipping black check")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "--diff", str(code_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # black returns 0 if formatted, 1 if not, 2 if error
            # We just want to ensure it runs without crashing (exit code != 2)
            assert result.returncode != 2, f"Black configuration error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("black not installed in environment, skipping execution test")
        except subprocess.TimeoutExpired:
            pytest.skip("black check timed out")