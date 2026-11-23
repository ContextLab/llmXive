"""
Unit tests for the setup_linting module.
Verifies that configuration files are created correctly.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# We need to mock the subprocess calls to avoid actually installing packages during tests
# and to isolate the file creation logic.

def test_create_ruff_config_creates_file():
    """Test that create_ruff_config creates the .ruff.toml file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the PROJECT_ROOT to point to our temp directory
        import code.setup_linting as linting_module
        
        # Temporarily override the module's PROJECT_ROOT
        original_root = linting_module.PROJECT_ROOT
        linting_module.PROJECT_ROOT = Path(tmpdir)
        
        try:
            linting_module.create_ruff_config()
            
            config_path = Path(tmpdir) / ".ruff.toml"
            assert config_path.exists(), "Ruff config file was not created"
            
            with open(config_path, "r") as f:
                content = f.read()
            
            # Verify some expected content
            assert "select" in content
            assert "E" in content
            assert "target-version" in content
        finally:
            # Restore original
            linting_module.PROJECT_ROOT = original_root

def test_create_black_config_creates_or_updates_pyproject():
    """Test that create_black_config updates pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import code.setup_linting as linting_module
        
        pyproject_path = Path(tmpdir) / "pyproject.toml"
        
        # Test 1: Create new file
        linting_module.PROJECT_ROOT = Path(tmpdir)
        linting_module.create_black_config()
        
        assert pyproject_path.exists(), "pyproject.toml was not created"
        
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        assert "[tool.black]" in content
        assert "line-length = 88" in content
        
        # Test 2: Append to existing file
        with open(pyproject_path, "w") as f:
            f.write("# Existing content\n")
        
        linting_module.create_black_config()
        
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        assert "# Existing content" in content
        assert "[tool.black]" in content

def test_install_tools_calls_pip():
    """Test that install_tools attempts to install the correct packages."""
    with patch("code.setup_linting.subprocess.check_call") as mock_call:
        import code.setup_linting as linting_module
        
        linting_module.install_tools()
        
        # Verify pip install was called for ruff and black
        calls = mock_call.call_args_list
        assert len(calls) >= 2
        
        # Check that 'ruff' and 'black' were in the arguments
        pip_commands = [str(call) for call in calls]
        assert any("ruff" in call for call in pip_commands)
        assert any("black" in call for call in pip_commands)