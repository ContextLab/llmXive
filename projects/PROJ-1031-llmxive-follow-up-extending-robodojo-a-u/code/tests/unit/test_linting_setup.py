import pytest
import os
from pathlib import Path
import tomllib

class TestLintingSetup:
    """Verify that linting and formatting tools are configured."""

    @pytest.fixture
    def code_root(self):
        return Path(__file__).parent.parent.parent

    def test_pyproject_toml_exists(self, code_root):
        """Check that pyproject.toml exists in the code root."""
        pyproject_path = code_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in code/"

    def test_pyproject_has_black_config(self, code_root):
        """Check that pyproject.toml contains Black configuration."""
        pyproject_path = code_root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)

        assert "tool" in config, "pyproject.toml must have [tool] section"
        assert "black" in config["tool"], "pyproject.toml must have [tool.black] section"
        assert "line-length" in config["tool"]["black"], "Black must define line-length"

    def test_pyproject_has_ruff_config(self, code_root):
        """Check that pyproject.toml contains Ruff configuration."""
        pyproject_path = code_root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)

        assert "tool" in config, "pyproject.toml must have [tool] section"
        assert "ruff" in config["tool"], "pyproject.toml must have [tool.ruff] section"
        assert "select" in config["tool"]["ruff"], "Ruff must define select rules"

    def test_ruff_toml_exists(self, code_root):
        """Check that .ruff.toml exists (optional but recommended)."""
        ruff_config_path = code_root / ".ruff.toml"
        assert ruff_config_path.exists(), ".ruff.toml should exist in code/"

    def test_precommit_config_exists(self, code_root):
        """Check that .pre-commit-config.yaml exists."""
        precommit_path = code_root / ".pre-commit-config.yaml"
        assert precommit_path.exists(), ".pre-commit-config.yaml must exist in code/"

    def test_requirements_includes_tools(self, code_root):
        """Check that requirements.txt includes ruff and black."""
        req_path = code_root / "requirements.txt"
        assert req_path.exists(), "requirements.txt must exist"

        content = req_path.read_text().lower()
        assert "ruff" in content, "requirements.txt must include ruff"
        assert "black" in content, "requirements.txt must include black"