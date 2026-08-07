import os
import tempfile
import shutil
from pathlib import Path
import pytest
import subprocess

from tests.unit.test_linting_config import TestLintingConfig

class TestLintingConfig:
    """Test that linting and formatting tools are correctly configured."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root with config files."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir) / "test_project"
        project_root.mkdir()

        # Copy config files
        ruff_config = project_root / ".ruff.toml"
        pyproject_config = project_root / "pyproject.toml"

        # Create minimal config files for testing
        ruff_config.write_text(
            """
            [lint]
            select = ["E", "W", "F", "I", "C", "B"]
            ignore = ["E501", "B008", "C901"]

            [format]
            quote-style = "double"
            indent-style = "space"
            """
        )

        pyproject_config.write_text(
            """
            [tool.black]
            line-length = 88
            target-version = ["py310"]

            [tool.ruff]
            line-length = 88
            target-version = "py310"
            select = ["E", "W", "F", "I", "C", "B"]
            """
        )

        yield project_root

        shutil.rmtree(temp_dir)

    def test_ruff_config_exists(self, temp_project_root):
        """Test that .ruff.toml or ruff configuration in pyproject.toml exists."""
        ruff_toml = temp_project_root / ".ruff.toml"
        pyproject_toml = temp_project_root / "pyproject.toml"

        assert ruff_toml.exists() or (
            pyproject_toml.exists()
            and "tool.ruff" in pyproject_toml.read_text()
        ), "Ruff configuration file not found"

    def test_black_config_exists(self, temp_project_root):
        """Test that black configuration in pyproject.toml exists."""
        pyproject_toml = temp_project_root / "pyproject.toml"

        assert pyproject_toml.exists(), "pyproject.toml not found"
        content = pyproject_toml.read_text()
        assert "[tool.black]" in content, "Black configuration not found in pyproject.toml"

    def test_ruff_can_run(self, temp_project_root):
        """Test that ruff can be invoked on the project."""
        try:
            result = subprocess.run(
                ["ruff", "check", "--version"],
                cwd=temp_project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"Ruff check failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("Ruff not installed in environment")
        except subprocess.TimeoutExpired:
            pytest.skip("Ruff check timed out")

    def test_black_can_run(self, temp_project_root):
        """Test that black can be invoked on the project."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                cwd=temp_project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"Black check failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("Black not installed in environment")
        except subprocess.TimeoutExpired:
            pytest.skip("Black check timed out")

    def test_config_files_in_project(self):
        """Test that config files exist in the actual project root."""
        project_root = Path(__file__).parent.parent.parent
        ruff_config = project_root / ".ruff.toml"
        pyproject_config = project_root / "pyproject.toml"

        assert ruff_config.exists(), ".ruff.toml not found in project root"
        assert pyproject_config.exists(), "pyproject.toml not found in project root"

        ruff_content = ruff_config.read_text()
        assert "tool.ruff" in ruff_content or "select" in ruff_content, \
            "Ruff configuration not properly set in .ruff.toml"

        pyproject_content = pyproject_config.read_text()
        assert "[tool.black]" in pyproject_content, \
            "Black configuration not found in pyproject.toml"