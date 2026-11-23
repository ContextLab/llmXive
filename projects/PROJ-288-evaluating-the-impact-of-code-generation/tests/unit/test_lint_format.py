"""
Unit tests for linting and formatting configuration.
These tests verify that the project structure and configuration files exist.
"""
import os
from pathlib import Path

import pytest


class TestLintingConfig:
    """Tests for Ruff and Black configuration."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Return the project root directory."""
        return Path(__file__).resolve().parents[1]

    def test_pyproject_toml_exists(self, project_root: Path) -> None:
        """Verify pyproject.toml exists in the project root."""
        config_file = project_root / "pyproject.toml"
        assert config_file.exists(), "pyproject.toml must exist in the project root"

    def test_black_section_in_pyproject(self, project_root: Path) -> None:
        """Verify Black configuration exists in pyproject.toml."""
        config_file = project_root / "pyproject.toml"
        content = config_file.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        assert "line-length" in content, "Black config must define line-length"

    def test_ruff_section_in_pyproject(self, project_root: Path) -> None:
        """Verify Ruff configuration exists in pyproject.toml."""
        config_file = project_root / "pyproject.toml"
        content = config_file.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

    def test_lint_tool_exists(self, project_root: Path) -> None:
        """Verify the lint_and_format tool script exists."""
        tool_path = project_root / "code" / "tools" / "lint_and_format.py"
        assert tool_path.exists(), "code/tools/lint_and_format.py must exist"

    def test_lint_tool_has_main(self, project_root: Path) -> None:
        """Verify the lint tool has a main function."""
        tool_path = project_root / "code" / "tools" / "lint_and_format.py"
        content = tool_path.read_text()
        assert "def main()" in content, "lint_and_format.py must define a main() function"

    def test_lint_tool_imports_subprocess(self, project_root: Path) -> None:
        """Verify the lint tool imports subprocess."""
        tool_path = project_root / "code" / "tools" / "lint_and_format.py"
        content = tool_path.read_text()
        assert "import subprocess" in content, "lint_and_format.py must import subprocess"