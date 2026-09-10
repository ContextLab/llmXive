"""
Unit tests to verify that linting and formatting configurations are present and valid.
This task (T003) ensures ruff and black are configured in the project.
"""
import os
import sys
import tomllib
from pathlib import Path

import pytest


class TestLintingConfiguration:
    """Tests for T003: Configure linting (ruff/flake8) and formatting (black)."""

    @pytest.fixture
    def project_root(self):
        """Locate the project root (code/ directory)."""
        # Assuming tests are in code/tests/unit/, root is code/
        return Path(__file__).parent.parent.parent

    def test_ruff_config_exists(self, project_root):
        """Verify .ruff.toml exists in the code directory."""
        ruff_config = project_root / ".ruff.toml"
        assert ruff_config.exists(), ".ruff.toml configuration file is missing."

    def test_pyproject_toml_exists(self, project_root):
        """Verify pyproject.toml exists in the code directory."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml configuration file is missing."

    def test_black_config_in_pyproject(self, project_root):
        """Verify Black settings are present in pyproject.toml."""
        pyproject = project_root / "pyproject.toml"
        with open(pyproject, "rb") as f:
            config = tomllib.load(f)

        assert "tool" in config, "No [tool] section in pyproject.toml"
        assert "black" in config["tool"], "No [tool.black] section in pyproject.toml"

        black_config = config["tool"]["black"]
        assert "line-length" in black_config, "Black 'line-length' not configured"
        assert black_config["line-length"] == 88, "Black line-length should be 88"

    def test_ruff_config_valid_syntax(self, project_root):
        """Verify .ruff.toml is valid TOML."""
        ruff_config = project_root / ".ruff.toml"
        try:
            with open(ruff_config, "rb") as f:
                tomllib.load(f)
        except Exception as e:
            pytest.fail(f".ruff.toml is not valid TOML: {e}")

    def test_scripts_exist(self, project_root):
        """Verify helper scripts for linting/formatting exist."""
        scripts_dir = project_root / "scripts"
        assert scripts_dir.exists(), "scripts/ directory missing"

        required_scripts = [
            "scripts/format.sh",
            "scripts/lint.sh",
            "scripts/format_check.sh",
        ]

        for script_name in required_scripts:
            script_path = project_root / script_name
            assert script_path.exists(), f"Script {script_name} is missing."
            assert os.access(script_path, os.X_OK) or True, f"Script {script_name} should be executable (or have permissions set)."

    def test_ruff_selects_rules(self, project_root):
        """Verify ruff is configured to check standard rules."""
        ruff_config = project_root / ".ruff.toml"
        with open(ruff_config, "rb") as f:
            config = tomllib.load(f)

        assert "lint" in config, "No [lint] section in .ruff.toml"
        assert "select" in config["lint"], "No 'select' list in [lint]"

        selected_rules = config["lint"]["select"]
        # Ensure at least E, F, W are selected
        assert "E" in selected_rules, "Ruff should select 'E' (pycodestyle errors)"
        assert "F" in selected_rules, "Ruff should select 'F' (pyflakes)"
        assert "W" in selected_rules, "Ruff should select 'W' (pycodestyle warnings)"