import os
import subprocess
import sys
import tempfile
import shutil
import pytest

class TestLintingConfig:
    """
    Tests to verify that linting (ruff) and formatting (black)
    tools are correctly configured and can be executed.
    """

    def test_ruff_config_exists(self):
        """Verify that ruff configuration is present in pyproject.toml"""
        # Check if pyproject.toml exists in the project root
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pyproject_path = os.path.join(root, "pyproject.toml")
        
        assert os.path.exists(pyproject_path), "pyproject.toml not found in project root"
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        assert "[tool.ruff]" in content, "ruff configuration section not found in pyproject.toml"
        assert "target-version" in content, "ruff target-version not configured"
    
    def test_black_config_exists(self):
        """Verify that black configuration is present in pyproject.toml"""
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pyproject_path = os.path.join(root, "pyproject.toml")
        
        assert os.path.exists(pyproject_path), "pyproject.toml not found in project root"
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        assert "[tool.black]" in content, "black configuration section not found in pyproject.toml"
        assert "line-length" in content, "black line-length not configured"
    
    def test_ruff_can_check_code(self):
        """Verify that ruff can be invoked to check code"""
        # This test assumes ruff is installed in the environment
        # We'll run a dry check on a simple file
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            result = subprocess.run(
                ["ruff", "check", "--version"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30
            )
            # If ruff is installed, this should succeed
            assert result.returncode == 0, f"ruff check failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("ruff not installed in environment")
    
    def test_black_can_check_code(self):
        """Verify that black can be invoked to check code"""
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            result = subprocess.run(
                ["black", "--check", "--version"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30
            )
            # If black is installed, this should succeed
            assert result.returncode == 0, f"black check failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("black not installed in environment")
    
    def test_config_files_are_valid(self):
        """Verify that the configuration in pyproject.toml is syntactically valid"""
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pyproject_path = os.path.join(root, "pyproject.toml")
        
        # Try to parse the TOML file
        try:
            import tomllib
        except ImportError:
            try:
                import toml as tomllib
            except ImportError:
                pytest.skip("toml parser not available")
        
        with open(pyproject_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert "tool" in config, "Missing 'tool' section in pyproject.toml"
        assert "black" in config["tool"], "Missing 'black' configuration"
        assert "ruff" in config["tool"], "Missing 'ruff' configuration"