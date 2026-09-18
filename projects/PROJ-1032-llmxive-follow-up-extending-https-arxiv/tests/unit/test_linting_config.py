"""
Unit tests to verify that linting and formatting tools are correctly configured.
These tests ensure that the project structure includes the necessary configuration
files for ruff and black as per task T003.
"""
import os
import toml
import yaml
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"
PRE_COMMIT_PATH = ROOT_DIR / ".pre-commit-config.yaml"
FORMAT_SCRIPT_PATH = ROOT_DIR / "scripts" / "format.sh"
LINT_SCRIPT_PATH = ROOT_DIR / "scripts" / "lint.sh"


class TestLintingConfiguration:
    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in the project root."""
        assert PYPROJECT_PATH.exists(), "pyproject.toml must exist in project root"

    def test_pyproject_has_ruff_config(self):
        """Verify ruff configuration is present in pyproject.toml."""
        assert PYPROJECT_PATH.exists()
        with open(PYPROJECT_PATH, "r") as f:
            config = toml.load(f)

        assert "tool" in config, "pyproject.toml must contain [tool] section"
        assert "ruff" in config["tool"], "pyproject.toml must contain [tool.ruff]"
        assert "line-length" in config["tool"]["ruff"], "Ruff must define line-length"
        assert "select" in config["tool"]["ruff"], "Ruff must define select rules"

    def test_pyproject_has_black_config(self):
        """Verify black configuration is present in pyproject.toml."""
        assert PYPROJECT_PATH.exists()
        with open(PYPROJECT_PATH, "r") as f:
            config = toml.load(f)

        assert "tool" in config, "pyproject.toml must contain [tool] section"
        assert "black" in config["tool"], "pyproject.toml must contain [tool.black]"
        assert "line-length" in config["tool"]["black"], "Black must define line-length"
        assert "target-version" in config["tool"]["black"], "Black must define target-version"

    def test_pre_commit_config_exists(self):
        """Verify .pre-commit-config.yaml exists."""
        assert PRE_COMMIT_PATH.exists(), ".pre-commit-config.yaml must exist"

    def test_pre_commit_has_ruff_hook(self):
        """Verify pre-commit config includes ruff hook."""
        assert PRE_COMMIT_PATH.exists()
        with open(PRE_COMMIT_PATH, "r") as f:
            config = yaml.safe_load(f)

        assert "repos" in config, "pre-commit config must have 'repos'"
        ruff_repo_found = False
        for repo in config["repos"]:
            if "ruff" in repo.get("repo", ""):
                ruff_repo_found = True
                hooks = repo.get("hooks", [])
                assert any(h.get("id") == "ruff" for h in hooks), "Ruff repo must have 'ruff' hook"
        assert ruff_repo_found, "pre-commit config must include ruff repository"

    def test_pre_commit_has_black_hook(self):
        """Verify pre-commit config includes black hook."""
        assert PRE_COMMIT_PATH.exists()
        with open(PRE_COMMIT_PATH, "r") as f:
            config = yaml.safe_load(f)

        assert "repos" in config, "pre-commit config must have 'repos'"
        black_repo_found = False
        for repo in config["repos"]:
            if "black" in repo.get("repo", ""):
                black_repo_found = True
                hooks = repo.get("hooks", [])
                assert any(h.get("id") == "black" for h in hooks), "Black repo must have 'black' hook"
        assert black_repo_found, "pre-commit config must include black repository"

    def test_format_script_exists(self):
        """Verify format.sh script exists."""
        assert FORMAT_SCRIPT_PATH.exists(), "scripts/format.sh must exist"

    def test_format_script_is_executable_content(self):
        """Verify format.sh contains black and ruff commands."""
        assert FORMAT_SCRIPT_PATH.exists()
        with open(FORMAT_SCRIPT_PATH, "r") as f:
            content = f.read()

        assert "black" in content, "format.sh must call black"
        assert "ruff" in content, "format.sh must call ruff"

    def test_lint_script_exists(self):
        """Verify lint.sh script exists."""
        assert LINT_SCRIPT_PATH.exists(), "scripts/lint.sh must exist"

    def test_lint_script_is_executable_content(self):
        """Verify lint.sh contains ruff command."""
        assert LINT_SCRIPT_PATH.exists()
        with open(LINT_SCRIPT_PATH, "r") as f:
            content = f.read()

        assert "ruff" in content, "lint.sh must call ruff"