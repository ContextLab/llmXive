"""
Tests to verify that linting configuration is properly set up.
These tests check that configuration files exist and contain expected settings.
"""
import os
import sys
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

class TestLintingConfiguration:
    """Test cases for linting configuration files."""

    def test_flake8_config_exists(self):
        """Test that .flake8 configuration file exists."""
        flake8_path = code_dir / ".flake8"
        assert flake8_path.exists(), f".flake8 file not found at {flake8_path}"

    def test_flake8_config_content(self):
        """Test that .flake8 contains expected configuration."""
        flake8_path = code_dir / ".flake8"
        content = flake8_path.read_text()

        # Check for required settings
        assert "max-line-length" in content.lower(), "max-line-length not configured in .flake8"
        assert "100" in content, "max-line-length should be set to 100"
        assert "ignore" in content.lower(), "ignore setting not configured in .flake8"
        assert "exclude" in content.lower(), "exclude setting not configured in .flake8"

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists."""
        pyproject_path = code_dir / "pyproject.toml"
        assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

    def test_black_configuration(self):
        """Test that black configuration exists in pyproject.toml."""
        pyproject_path = code_dir / "pyproject.toml"
        content = pyproject_path.read_text()

        assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"
        assert "line-length" in content.lower(), "Black line-length not configured"
        assert "100" in content, "Black line-length should be 100"

    def test_isort_configuration(self):
        """Test that isort configuration exists in pyproject.toml."""
        pyproject_path = code_dir / "pyproject.toml"
        content = pyproject_path.read_text()

        assert "[tool.isort]" in content, "isort configuration section not found in pyproject.toml"
        assert "profile" in content.lower(), "isort profile not configured"
        assert "black" in content.lower(), "isort should use black profile"

    def test_setup_linting_script_exists(self):
        """Test that setup_linting.py script exists."""
        script_path = code_dir / "setup_linting.py"
        assert script_path.exists(), f"setup_linting.py not found at {script_path}"

    def test_setup_linting_script_content(self):
        """Test that setup_linting.py contains expected functions."""
        script_path = code_dir / "setup_linting.py"
        content = script_path.read_text()

        assert "def run_command" in content, "run_command function not found in setup_linting.py"
        assert "def main" in content, "main function not found in setup_linting.py"
        assert "flake8" in content.lower(), "flake8 installation not referenced in setup_linting.py"
        assert "black" in content.lower(), "black installation not referenced in setup_linting.py"
        assert "isort" in content.lower(), "isort installation not referenced in setup_linting.py"

    def test_linting_tools_installation_logic(self):
        """Test that setup_linting.py includes proper installation logic."""
        script_path = code_dir / "setup_linting.py"
        content = script_path.read_text()

        # Check for pip installation command
        assert "pip install" in content.lower(), "pip installation logic not found"
        assert "subprocess" in content, "subprocess module not imported for command execution"
        assert "sys.executable" in content, "sys.executable not used for Python path"

    def test_linting_excludes_data_results(self):
        """Test that linting configuration excludes data and results directories."""
        flake8_path = code_dir / ".flake8"
        pyproject_path = code_dir / "pyproject.toml"

        flake8_content = flake8_path.read_text()
        pyproject_content = pyproject_path.read_text()

        # Check that data and results are excluded
        assert "data" in flake8_content.lower() or "data" in pyproject_content.lower(), \
            "data directory should be excluded from linting"
        assert "results" in flake8_content.lower() or "results" in pyproject_content.lower(), \
            "results directory should be excluded from linting"