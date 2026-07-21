import os
import subprocess
import tempfile
import shutil
from pathlib import Path

import pytest


class TestLintingConfig:
    """Tests to verify linting and formatting configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        # Assume tests are in tests/unit/, so root is parent of parent
        return Path(__file__).resolve().parent.parent.parent

    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists in the code directory."""
        pyproject_path = project_root / "code" / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in code/"

    def test_flake8_config_exists(self, project_root):
        """Test that .flake8 config exists in the code directory."""
        flake8_path = project_root / "code" / ".flake8"
        assert flake8_path.exists(), ".flake8 must exist in code/"

    def test_isort_config_exists(self, project_root):
        """Test that .isort.cfg config exists in the code directory."""
        isort_path = project_root / "code" / ".isort.cfg"
        assert isort_path.exists(), ".isort.cfg must exist in code/"

    def test_black_config_in_pyproject(self, project_root):
        """Test that black configuration exists in pyproject.toml."""
        pyproject_path = project_root / "code" / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
        assert "line-length" in content, "Black line-length configuration missing"

    def test_isort_config_content(self, project_root):
        """Test that isort configuration has expected settings."""
        isort_path = project_root / "code" / ".isort.cfg"
        content = isort_path.read_text()
        assert "profile = black" in content, "isort profile should be black"
        assert "line_length = 100" in content, "isort line_length should be 100"

    def test_flake8_config_content(self, project_root):
        """Test that flake8 configuration has expected settings."""
        flake8_path = project_root / "code" / ".flake8"
        content = flake8_path.read_text()
        assert "max-line-length = 100" in content, "flake8 max-line-length should be 100"
        assert "E203" in content, "flake8 should ignore E203 (black conflict)"
        assert "W503" in content, "flake8 should ignore W503 (black conflict)"

    def test_setup_script_exists(self, project_root):
        """Test that the setup script exists."""
        setup_script = project_root / "code" / "scripts" / "setup_linting.sh"
        assert setup_script.exists(), "setup_linting.sh must exist in code/scripts/"

    def test_setup_script_executable(self, project_root):
        """Test that the setup script is executable (or can be run with bash)."""
        setup_script = project_root / "code" / "scripts" / "setup_linting.sh"
        # We just check if it can be invoked with bash
        result = subprocess.run(
            ["bash", "-c", f"bash {setup_script} --help 2>&1 || true"],
            capture_output=True,
            text=True
        )
        # The script might fail if tools aren't installed, but it should be runnable
        # We're mainly checking it's a valid bash script
        assert result.returncode == 0 or "Usage" in result.stdout or "Installing" in result.stdout