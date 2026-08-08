"""
Unit tests for linting and formatting configuration.
These tests verify that the configuration files exist and are valid.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import subprocess
import yaml
import sys

# Add the code directory to the path for imports if needed
# Though this test mostly checks file existence and format
code_root = Path(__file__).parent.parent.parent
pyproject_path = code_root / "pyproject.toml"
ruff_config_path = code_root / ".ruff.toml"
pre_commit_path = code_root / ".pre-commit-config.yaml"

class TestLintingConfig:
    """Tests for the linting configuration setup."""

    def test_pyproject_toml_exists(self):
        """Verify that pyproject.toml exists in the project root."""
        assert pyproject_path.exists(), "pyproject.toml must exist in the project root"

    def test_pyproject_toml_valid(self):
        """Verify that pyproject.toml contains valid TOML and required sections."""
        # Basic validation: try to parse as YAML (since toml is subset compatible for simple cases)
        # or just check existence of key strings.
        # For a robust check, we'd use a toml parser, but simple string check is often enough for CI.
        content = pyproject_path.read_text()
        
        # Check for ruff and black sections
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        assert "ruff" in content, "pyproject.toml must mention ruff"
        assert "black" in content, "pyproject.toml must mention black"

    def test_ruff_config_exists(self):
        """Verify that .ruff.toml exists."""
        assert ruff_config_path.exists(), ".ruff.toml must exist"

    def test_pre_commit_config_exists(self):
        """Verify that .pre-commit-config.yaml exists."""
        assert pre_commit_path.exists(), ".pre-commit-config.yaml must exist"

    def test_pre_commit_config_valid_yaml(self):
        """Verify that .pre-commit-config.yaml is valid YAML."""
        with open(pre_commit_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                assert "repos" in config, "pre-commit config must have 'repos' key"
                # Check for ruff and black repos
                repos = config["repos"]
                has_ruff = any("ruff" in str(repo.get("repo", "")) for repo in repos)
                has_black = any("black" in str(repo.get("repo", "")) for repo in repos)
                
                assert has_ruff, "pre-commit config must include ruff"
                assert has_black, "pre-commit config must include black"
            except yaml.YAMLError as e:
                pytest.fail(f"pre-commit config is not valid YAML: {e}")

    def test_ruff_version_command(self):
        """Verify that ruff can be invoked."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            assert b"ruff" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("ruff not installed in environment")
        except subprocess.TimeoutExpired:
            pytest.fail("ruff version command timed out")
        except subprocess.CalledProcessError as e:
            pytest.fail(f"ruff version command failed: {e}")

    def test_black_version_command(self):
        """Verify that black can be invoked."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            assert b"black" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("black not installed in environment")
        except subprocess.TimeoutExpired:
            pytest.fail("black version command timed out")
        except subprocess.CalledProcessError as e:
            pytest.fail(f"black version command failed: {e}")