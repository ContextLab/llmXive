import pytest
import os
from pathlib import Path
import tomllib

class TestLintingSetup:
    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in code/ directory."""
        project_root = Path(__file__).resolve().parent.parent.parent
        pyproject_path = project_root / "code" / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in code/ directory"

    def test_black_config_present(self):
        """Verify Black configuration is present in pyproject.toml."""
        project_root = Path(__file__).resolve().parent.parent.parent
        pyproject_path = project_root / "code" / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)

        assert "tool" in config, "pyproject.toml must contain [tool] section"
        assert "black" in config["tool"], "Black configuration missing from pyproject.toml"
        assert "line-length" in config["tool"]["black"], "Black line-length must be configured"
        assert config["tool"]["black"]["line-length"] == 88, "Black line-length should be 88"

    def test_ruff_config_present(self):
        """Verify Ruff configuration is present in pyproject.toml."""
        project_root = Path(__file__).resolve().parent.parent.parent
        pyproject_path = project_root / "code" / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)

        assert "tool" in config, "pyproject.toml must contain [tool] section"
        assert "ruff" in config["tool"], "Ruff configuration missing from pyproject.toml"
        assert "select" in config["tool"]["ruff"], "Ruff select rules must be configured"

    def test_ruff_toml_exists(self):
        """Verify .ruff.toml exists in code/ directory."""
        project_root = Path(__file__).resolve().parent.parent.parent
        ruff_toml_path = project_root / "code" / ".ruff.toml"
        assert ruff_toml_path.exists(), ".ruff.toml must exist in code/ directory"

    def test_pre_commit_config_exists(self):
        """Verify .pre-commit-config.yaml exists in code/ directory."""
        project_root = Path(__file__).resolve().parent.parent.parent
        pre_commit_path = project_root / "code" / ".pre-commit-config.yaml"
        assert pre_commit_path.exists(), ".pre-commit-config.yaml must exist in code/ directory"

    def test_requirements_includes_linting_tools(self):
        """Verify requirements.txt includes ruff and black."""
        project_root = Path(__file__).resolve().parent.parent.parent
        requirements_path = project_root / "code" / "requirements.txt"

        with open(requirements_path, "r") as f:
            content = f.read().lower()

        assert "ruff" in content, "requirements.txt must include ruff"
        assert "black" in content, "requirements.txt must include black"