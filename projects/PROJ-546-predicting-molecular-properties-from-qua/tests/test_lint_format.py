"""
Unit tests for linting and formatting configuration.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestLintFormatConfig:
    """Tests for linting and formatting setup."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists in the project root."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in project root"

    def test_pyproject_contains_black_config(self, project_root):
        """Test that pyproject.toml contains Black configuration."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        assert "line-length" in content, "Black configuration must specify line-length"

    def test_pyproject_contains_ruff_config(self, project_root):
        """Test that pyproject.toml contains Ruff configuration."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
        assert "select" in content, "Ruff configuration must specify rules to select"

    def test_ruff_toml_exists_or_config_in_pyproject(self, project_root):
        """Test that either .ruff.toml exists or config is in pyproject.toml."""
        ruff_toml_path = project_root / ".ruff.toml"
        pyproject_path = project_root / "pyproject.toml"

        has_ruff_toml = ruff_toml_path.exists()
        has_config_in_pyproject = "[tool.ruff]" in pyproject_path.read_text()

        assert has_ruff_toml or has_config_in_pyproject, (
            "Either .ruff.toml must exist or Ruff config must be in pyproject.toml"
        )

    def test_ruff_check_passes_on_empty(self, project_root):
        """Test that ruff check passes on an empty codebase (no Python files)."""
        # Create a temporary empty Python file to test ruff
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"")
            temp_file = f.name

        try:
            result = subprocess.run(
                ["ruff", "check", temp_file],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            # Ruff should return 0 for an empty file
            assert result.returncode == 0, f"Ruff check failed: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_black_check_passes_on_empty(self, project_root):
        """Test that black --check passes on an empty codebase (no Python files)."""
        # Create a temporary empty Python file to test black
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"")
            temp_file = f.name

        try:
            result = subprocess.run(
                ["black", "--check", temp_file],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            # Black should return 0 for an empty file
            assert result.returncode == 0, f"Black check failed: {result.stderr}"
        finally:
            os.unlink(temp_file)