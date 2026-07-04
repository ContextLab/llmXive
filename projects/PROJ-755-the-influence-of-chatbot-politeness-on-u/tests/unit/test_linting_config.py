"""
Unit tests for linting configuration generation (Task T003).
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function we are testing
from code.setup_linting import create_ruff_config, create_black_config, main

class TestLintingConfig:
    """Tests for the linting configuration generation."""

    def test_ruff_config_content(self):
        """Verify ruff.toml content contains expected sections."""
        content = create_ruff_config()
        
        assert "[lint]" in content
        assert "select" in content
        assert "E" in content  # pycodestyle
        assert "F" in content  # Pyflakes
        assert "target-version" in content
        assert "py311" in content

    def test_black_config_content(self):
        """Verify black config content contains expected settings."""
        content = create_black_config()
        
        assert "[tool.black]" in content
        assert "line-length" in content
        assert "88" in content
        assert "target-version" in content
        assert "py311" in content

    def test_main_creates_files(self):
        """Verify that main() creates the necessary files."""
        # Create a temporary directory to simulate the project root
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Run the main function
                main()
                
                # Check that files were created
                assert os.path.exists("ruff.toml"), "ruff.toml was not created"
                assert os.path.exists("pyproject.toml"), "pyproject.toml was not created"
                assert os.path.exists("requirements.txt"), "requirements.txt was not updated"
                
                # Verify content
                with open("ruff.toml", "r") as f:
                    ruff_content = f.read()
                    assert "[lint]" in ruff_content
                
                with open("pyproject.toml", "r") as f:
                    pyproject_content = f.read()
                    assert "[tool.black]" in pyproject_content
                
                with open("requirements.txt", "r") as f:
                    req_content = f.read()
                    assert "ruff" in req_content.lower()
                    assert "black" in req_content.lower()
                    
            finally:
                os.chdir(original_cwd)

    def test_pyproject_append_logic(self):
        """Verify that black config is appended correctly to existing pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create a dummy pyproject.toml with existing content
                with open("pyproject.toml", "w") as f:
                    f.write("# Existing content\n[tool.some_other]\nkey = 'value'\n")
                
                # Run main
                main()
                
                # Read the file and ensure it has both old and new content
                with open("pyproject.toml", "r") as f:
                    content = f.read()
                    
                assert "# Existing content" in content
                assert "[tool.black]" in content
                
            finally:
                os.chdir(original_cwd)