"""Integration tests for linting and formatting configuration."""
import os
import sys
import subprocess
from pathlib import Path
import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_linting import get_project_root, run_command


class TestLintingIntegration:
    """Integration tests for linting and formatting tools."""

    @pytest.fixture(scope="class")
    def project_root(self):
        """Get the project root directory."""
        return get_project_root()

    def test_ruff_installed(self, project_root):
        """Test that ruff is installed and can be run."""
        # Try to run ruff --version
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert result.returncode == 0
        assert "ruff" in result.stdout.lower()

    def test_black_installed(self, project_root):
        """Test that black is installed and can be run."""
        # Try to run black --version
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert result.returncode == 0
        assert "black" in result.stdout.lower()

    def test_ruff_config_exists(self, project_root):
        """Test that ruff configuration file exists."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists()
        
        content = pyproject.read_text()
        assert "[tool.ruff]" in content

    def test_black_config_exists(self, project_root):
        """Test that black configuration file exists."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists()
        
        content = pyproject.read_text()
        assert "[tool.black]" in content

    def test_ruff_can_check_code(self, project_root):
        """Test that ruff can run on the codebase."""
        # Run ruff check on the code directory
        result = subprocess.run(
            ["ruff", "check", "code"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # Return code 0 means no errors, 1 means found issues (both are ok for this test)
        # We just want to ensure ruff runs without crashing
        assert result.returncode in [0, 1]

    def test_black_can_check_code(self, project_root):
        """Test that black can run on the codebase."""
        # Run black --check on the code directory
        result = subprocess.run(
            ["black", "--check", "code"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # Return code 0 means all good, 1 means some files need formatting (both ok)
        # We just want to ensure black runs without crashing
        assert result.returncode in [0, 1]

    def test_requirements_includes_linting_tools(self, project_root):
        """Test that requirements.txt includes linting tools."""
        requirements = project_root / "requirements.txt"
        assert requirements.exists()
        
        content = requirements.read_text().lower()
        assert "ruff" in content
        assert "black" in content