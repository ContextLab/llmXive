"""
Test suite for T002b: Verify linting and formatting configuration.
This test ensures that pyproject.toml and .ruff.toml exist and are valid.
It does NOT run the linters (as they require installation), but verifies
the configuration files are present and non-empty.
"""
import os
from pathlib import Path

import pytest


class TestLintingConfig:
    """Tests for linting and formatting configuration files."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Return the project root directory."""
        return Path(__file__).resolve().parent.parent

    def test_pyproject_toml_exists(self, project_root: Path):
        """Verify pyproject.toml exists in the code directory."""
        config_path = project_root / "code" / "pyproject.toml"
        assert config_path.exists(), f"pyproject.toml not found at {config_path}"
        assert config_path.stat().st_size > 0, "pyproject.toml is empty"

    def test_ruff_config_exists(self, project_root: Path):
        """Verify .ruff.toml exists in the code directory."""
        config_path = project_root / "code" / ".ruff.toml"
        assert config_path.exists(), f".ruff.toml not found at {config_path}"
        assert config_path.stat().st_size > 0, ".ruff.toml is empty"

    def test_pyproject_toml_contains_black_config(self, project_root: Path):
        """Verify pyproject.toml contains Black configuration."""
        config_path = project_root / "code" / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.black]" in content, "Black configuration section missing"
        assert "line-length" in content, "Black line-length setting missing"

    def test_pyproject_toml_contains_ruff_config(self, project_root: Path):
        """Verify pyproject.toml contains Ruff configuration."""
        config_path = project_root / "code" / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration section missing"
        assert "select" in content, "Ruff select rule missing"

    def test_ruff_toml_contains_select_rules(self, project_root: Path):
        """Verify .ruff.toml contains valid select rules."""
        config_path = project_root / "code" / ".ruff.toml"
        content = config_path.read_text()
        assert "select" in content, "Select rules missing in .ruff.toml"
        assert "line-length" in content, "Line-length setting missing in .ruff.toml"