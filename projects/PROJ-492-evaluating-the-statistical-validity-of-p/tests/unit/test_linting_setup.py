"""
Unit tests for linting and formatting setup (T003).

These tests verify that:
1. Pre-commit configuration file exists and is valid YAML
2. pyproject.toml contains ruff and black configuration
3. Required tools can be imported/used
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestPreCommitConfig:
    """Tests for .pre-commit-config.yaml"""

    def test_pre_commit_config_exists(self):
        """Verify pre-commit config file exists at project root."""
        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        assert config_path.exists(), ".pre-commit-config.yaml must exist at project root"

    def test_pre_commit_config_is_valid_yaml(self):
        """Verify pre-commit config is valid YAML."""
        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            assert config is not None, "Config file should not be empty"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")

    def test_pre_commit_config_has_ruff_hook(self):
        """Verify ruff hook is configured."""
        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        repos = config.get("repos", [])
        ruff_repos = [r for r in repos if "ruff" in r.get("repo", "")]
        assert len(ruff_repos) > 0, "ruff hook must be configured"

        # Check for ruff and ruff-format hooks
        hooks = ruff_repos[0].get("hooks", [])
        hook_ids = [h.get("id") for h in hooks]
        assert "ruff" in hook_ids, "ruff linter hook must be configured"

    def test_pre_commit_config_has_black_hook(self):
        """Verify black hook is configured."""
        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        repos = config.get("repos", [])
        black_repos = [r for r in repos if "black" in r.get("repo", "")]
        assert len(black_repos) > 0, "black hook must be configured"

        hooks = black_repos[0].get("hooks", [])
        hook_ids = [h.get("id") for h in hooks]
        assert "black" in hook_ids, "black formatter hook must be configured"


class TestPyProjectConfig:
    """Tests for pyproject.toml configuration"""

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists at project root."""
        config_path = PROJECT_ROOT / "pyproject.toml"
        assert config_path.exists(), "pyproject.toml must exist at project root"

    def test_pyproject_has_ruff_config(self):
        """Verify pyproject.toml contains ruff configuration."""
        config_path = PROJECT_ROOT / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

    def test_pyproject_has_black_config(self):
        """Verify pyproject.toml contains black configuration."""
        config_path = PROJECT_ROOT / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

    def test_pyproject_has_ruff_line_length(self):
        """Verify ruff line-length is set to 88 (black compatible)."""
        config_path = PROJECT_ROOT / "pyproject.toml"
        content = config_path.read_text()
        assert "line-length = 88" in content, "ruff line-length should be 88 for black compatibility"


class TestSetupScript:
    """Tests for the setup_linting.py script"""

    def test_setup_script_exists(self):
        """Verify setup_linting.py exists."""
        script_path = PROJECT_ROOT / "code" / "setup_linting.py"
        assert script_path.exists(), "code/setup_linting.py must exist"

    def test_setup_script_is_valid_python(self):
        """Verify setup_linting.py is syntactically valid Python."""
        script_path = PROJECT_ROOT / "code" / "setup_linting.py"
        try:
            compile(script_path.read_text(), script_path, "exec")
        except SyntaxError as e:
            pytest.fail(f"setup_linting.py has syntax errors: {e}")

    def test_setup_script_imports(self):
        """Verify setup_linting.py has correct imports."""
        script_path = PROJECT_ROOT / "code" / "setup_linting.py"
        content = script_path.read_text()
        required_imports = ["subprocess", "sys", "pathlib"]
        for imp in required_imports:
            assert imp in content, f"setup_linting.py must import {imp}"


class TestToolAvailability:
    """Tests for tool availability"""

    @pytest.mark.skipif(
        os.environ.get("SKIP_TOOL_TESTS") == "1",
        reason="Skipping tool availability tests",
    )
    def test_ruff_is_available(self):
        """Verify ruff is available in PATH."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"ruff not available: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("ruff not installed in test environment")

    @pytest.mark.skipif(
        os.environ.get("SKIP_TOOL_TESTS") == "1",
        reason="Skipping tool availability tests",
    )
    def test_black_is_available(self):
        """Verify black is available in PATH."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"black not available: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("black not installed in test environment")
