"""
Unit tests to verify that linting and formatting configurations are correctly set up.
"""
import pytest
import os
from pathlib import Path
import tomllib

class TestLintingSetup:
    """Tests for linting configuration files."""

    @pytest.fixture
    def code_dir(self):
        """Return the code directory path."""
        return Path(__file__).resolve().parent.parent.parent

    def test_pyproject_toml_exists(self, code_dir):
        """Test that pyproject.toml exists."""
        assert (code_dir / "pyproject.toml").exists(), "pyproject.toml must exist"

    def test_pyproject_toml_valid(self, code_dir):
        """Test that pyproject.toml is valid TOML and contains required sections."""
        pyproject_path = code_dir / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)

        # Check for black configuration
        assert "tool" in config, "pyproject.toml must have 'tool' section"
        assert "black" in config["tool"], "pyproject.toml must contain [tool.black]"
        assert config["tool"]["black"].get("line-length") == 100, "Black line-length must be 100"

        # Check for ruff configuration
        assert "ruff" in config["tool"], "pyproject.toml must contain [tool.ruff]"

    def test_ruff_toml_exists(self, code_dir):
        """Test that .ruff.toml exists."""
        assert (code_dir / ".ruff.toml").exists(), ".ruff.toml must exist"

    def test_precommit_config_exists(self, code_dir):
        """Test that .pre-commit-config.yaml exists."""
        assert (code_dir / ".pre-commit-config.yaml").exists(), ".pre-commit-config.yaml must exist"

    def test_precommit_config_valid(self, code_dir):
        """Test that .pre-commit-config.yaml contains ruff and black hooks."""
        import yaml
        config_path = code_dir / ".pre-commit-config.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        repos = config.get("repos", [])
        hook_ids = []
        for repo in repos:
            for hook in repo.get("hooks", []):
                hook_ids.append(hook.get("id"))

        assert "ruff" in hook_ids or "ruff-check" in hook_ids, "Pre-commit must include ruff hook"
        assert "black" in hook_ids, "Pre-commit must include black hook"

    def test_black_line_length_matches_ruff(self, code_dir):
        """Test that black and ruff line-length settings are consistent."""
        with open(code_dir / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
        with open(code_dir / ".ruff.toml", "r") as f:
            ruff_config = tomllib.load(f)

        black_len = pyproject["tool"]["black"]["line-length"]
        ruff_len = ruff_config["line-length"]

        assert black_len == ruff_len, f"Line lengths must match: black={black_len}, ruff={ruff_len}"