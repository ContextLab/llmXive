"""
Tests to verify that linting and formatting configurations are present and valid.
"""
import os
from pathlib import Path

import pytest


class TestLintingConfiguration:
    """Test suite for linting and formatting tool setup."""

    @pytest.fixture
    def project_root(self):
        """Return the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_flake8_config_exists(self, project_root):
        """Test that .flake8 configuration file exists."""
        config_path = project_root / "code" / ".flake8"
        assert config_path.exists(), f".flake8 not found at {config_path}"

    def test_black_config_exists(self, project_root):
        """Test that black configuration exists in pyproject.toml."""
        config_path = project_root / "code" / "pyproject.toml"
        assert config_path.exists(), f"pyproject.toml not found at {config_path}"
        
        content = config_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"

    def test_pylint_config_exists(self, project_root):
        """Test that pylint configuration exists in pyproject.toml."""
        config_path = project_root / "code" / "pyproject.toml"
        assert config_path.exists(), f"pyproject.toml not found at {config_path}"
        
        content = config_path.read_text()
        assert "[tool.pylint" in content, "Pylint configuration missing in pyproject.toml"

    def test_setup_linting_script_exists(self, project_root):
        """Test that the setup_linting.py script exists."""
        script_path = project_root / "code" / "setup_linting.py"
        assert script_path.exists(), f"setup_linting.py not found at {script_path}"

    def test_setup_linting_script_imports(self, project_root):
        """Test that setup_linting.py can be imported without errors."""
        # Add the code directory to the path
        code_dir = project_root / "code"
        if str(code_dir) not in os.sys.path:
            os.sys.path.insert(0, str(code_dir))
        
        try:
            import setup_linting
            assert hasattr(setup_linting, "run_command")
            assert hasattr(setup_linting, "main")
        finally:
            # Clean up path
            if str(code_dir) in os.sys.path:
                os.sys.path.remove(str(code_dir))
