"""
Tests for the linting and formatting configuration setup.
"""
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_linting import ensure_config_file, install_tools

def test_install_tools():
    """Test that install_tools returns a non-empty list of installed tools."""
    # Note: In a real CI environment, we might mock this to avoid actual pip installs
    # For now, we assume the environment has pip available
    result = install_tools()
    assert isinstance(result, list), "install_tools should return a list"
    # We expect at least one tool to be successfully installed/verified
    assert len(result) > 0, "At least one tool should be installed"
    assert "ruff" in result or "black" in result, "ruff or black should be in the list"

def test_ensure_config_file():
    """Test that ensure_config_file creates pyproject.toml with correct content."""
    # Create a temporary directory to simulate a project root
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pyproject_path = tmp_path / "pyproject.toml"
        
        # Temporarily change the working directory to simulate the project root
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Mock the function to use our temp directory
            # We need to patch the Path(__file__) resolution in the module
            # For simplicity, we'll just check if the file is created in the current dir
            result = ensure_config_file()
            
            assert "pyproject.toml" in result, "pyproject.toml should be in result keys"
            assert pyproject_path.exists(), "pyproject.toml should be created"
            
            content = pyproject_path.read_text()
            assert "[tool.black]" in content, "pyproject.toml should contain black config"
            assert "[tool.ruff]" in content, "pyproject.toml should contain ruff config"
            assert "line-length = 88" in content, "pyproject.toml should have line-length = 88"
            assert "target-version = ['py311']" in content or "target-version = \"py311\"" in content, "pyproject.toml should target Python 3.11"
            
        finally:
            os.chdir(original_cwd)

def test_config_content_structure():
    """Test that the generated config has the expected sections."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pyproject_path = tmp_path / "pyproject.toml"
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            ensure_config_file()
            content = pyproject_path.read_text()
            
            # Check for essential sections
            required_sections = [
                "[tool.black]",
                "[tool.ruff]",
                "[tool.ruff.isort]",
                "[tool.pytest.ini_options]"
            ]
            
            for section in required_sections:
                assert section in content, f"Config should contain {section}"
                
        finally:
            os.chdir(original_cwd)