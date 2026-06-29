"""
Unit tests for development dependency installation.

Tests verify that the dev dependency installation script works correctly
and that black formatter is properly configured.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest


class TestDevDependencies:
    """Tests for development dependency setup."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def requirements_dev_path(self, project_root):
        """Get path to requirements-dev.txt."""
        return project_root / 'code' / 'requirements-dev.txt'

    @pytest.fixture
    def install_dev_script(self, project_root):
        """Get path to install_dev_dependencies.py."""
        return project_root / 'code' / 'setup' / 'install_dev_dependencies.py'

    def test_requirements_dev_exists(self, requirements_dev_path):
        """Test that requirements-dev.txt exists."""
        assert requirements_dev_path.exists(), \
            "requirements-dev.txt should exist in code/"

    def test_black_in_requirements_dev(self, requirements_dev_path):
        """Test that black is listed in requirements-dev.txt."""
        content = requirements_dev_path.read_text()
        assert 'black' in content.lower(), \
            "black should be listed in requirements-dev.txt"

    def test_install_dev_script_exists(self, install_dev_script):
        """Test that install_dev_dependencies.py exists."""
        assert install_dev_script.exists(), \
            "install_dev_dependencies.py should exist in code/setup/"

    def test_install_dev_script_syntax(self, install_dev_script):
        """Test that install_dev_dependencies.py has valid Python syntax."""
        try:
            with open(install_dev_script, 'r') as f:
                compile(f.read(), str(install_dev_script), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in install_dev_dependencies.py: {e}")

    def test_install_dev_script_has_main(self, install_dev_script):
        """Test that install_dev_dependencies.py has a main function."""
        with open(install_dev_script, 'r') as f:
            content = f.read()
            assert 'def main()' in content or 'def main(' in content, \
                "install_dev_dependencies.py should have a main function"

    def test_install_dev_script_imports_required(self, install_dev_script):
        """Test that install_dev_dependencies.py imports required modules."""
        with open(install_dev_script, 'r') as f:
            content = f.read()
            required_imports = ['os', 'subprocess', 'sys', 'pathlib']
            for imp in required_imports:
                assert f'import {imp}' in content or f'from {imp}' in content, \
                    f"install_dev_dependencies.py should import {imp}"

    def test_black_can_be_imported(self):
        """Test that black can be imported (if installed)."""
        try:
            import black
            assert hasattr(black, 'format_str'), \
                "black module should have format_str function"
        except ImportError:
            pytest.skip("black not installed in test environment")

    def test_black_format_command_exists(self):
        """Test that black command is available (if installed)."""
        try:
            result = subprocess.run(
                ['black', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, \
                f"black --version failed: {result.stderr}"
            assert 'black' in result.stdout.lower(), \
                "black version output should contain 'black'"
        except FileNotFoundError:
            pytest.skip("black command not found in PATH")
        except subprocess.TimeoutExpired:
            pytest.skip("black version check timed out")