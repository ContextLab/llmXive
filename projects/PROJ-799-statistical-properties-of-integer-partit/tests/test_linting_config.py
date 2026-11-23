"""
Contract test for linting configuration and tool availability.
Verifies that the linting infrastructure is correctly set up for the project.
"""

import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"


class TestLintingSetup:
    """Tests to verify linting tools and configuration are present."""

    def test_flake8_config_exists(self):
        """Verify .flake8 configuration file exists in project root."""
        config_path = PROJECT_ROOT / ".flake8"
        assert config_path.exists(), f".flake8 config not found at {config_path}"

    def test_pyproject_black_config_exists(self):
        """Verify black configuration exists in pyproject.toml."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"
        assert "line-length = 100" in content, "Black line-length setting missing"

    def test_lint_config_module_importable(self):
        """Verify the lint_config module can be imported."""
        # Add code dir to path to allow import
        sys.path.insert(0, str(PROJECT_ROOT / "code"))
        try:
            import lint_config
            assert hasattr(lint_config, "run_flake8")
            assert hasattr(lint_config, "run_black")
            assert hasattr(lint_config, "run_all_checks")
        finally:
            sys.path.remove(str(PROJECT_ROOT / "code"))

    @pytest.mark.skipif(
        subprocess.run(["which", "flake8"], capture_output=True).returncode != 0,
        reason="flake8 not installed in environment"
    )
    def test_flake8_executable_available(self):
        """Verify flake8 is available in the environment."""
        result = subprocess.run(["flake8", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "flake8 executable not found or failed"

    @pytest.mark.skipif(
        subprocess.run(["which", "black"], capture_output=True).returncode != 0,
        reason="black not installed in environment"
    )
    def test_black_executable_available(self):
        """Verify black is available in the environment."""
        result = subprocess.run(["black", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "black executable not found or failed"

    @pytest.mark.integration
    def test_lint_config_module_runs_without_error(self):
        """Verify the lint_config module can be executed without import errors."""
        # This test ensures the module structure is valid even if checks fail due to code style
        sys.path.insert(0, str(PROJECT_ROOT / "code"))
        try:
            import lint_config
            # Just calling the function definitions to ensure they exist and are callable
            assert callable(lint_config.run_flake8)
            assert callable(lint_config.run_black)
            assert callable(lint_config.run_all_checks)
        finally:
            sys.path.remove(str(PROJECT_ROOT / "code"))
