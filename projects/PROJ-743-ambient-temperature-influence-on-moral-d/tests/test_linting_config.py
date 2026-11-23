"""
Tests for linting and formatting configuration (T009).

These tests verify that the linting configuration files (pyproject.toml,
.ruff.toml, .flake8) are correctly created and contain the expected settings.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
import tomli

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config_linting import (
    ensure_pyproject_toml,
    ensure_ruff_config,
    ensure_flake8_config,
)
from config import get_path_env_override


class TestLintingConfiguration:
    """Test suite for linting configuration generation."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate a project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the required directory structure
            Path(tmpdir, "code").mkdir()
            Path(tmpdir, "tests").mkdir()
            Path(tmpdir, "data").mkdir()
            
            # Set the environment variable to point to our temp directory
            original_value = os.environ.get("PROJECT_ROOT")
            os.environ["PROJECT_ROOT"] = tmpdir
            
            yield Path(tmpdir)
            
            # Restore the original environment variable
            if original_value:
                os.environ["PROJECT_ROOT"] = original_value
            elif "PROJECT_ROOT" in os.environ:
                del os.environ["PROJECT_ROOT"]

    def test_pyproject_toml_creation(self, temp_project_root):
        """Test that pyproject.toml is created with correct content."""
        pyproject_path = temp_project_root / "pyproject.toml"
        
        # Verify file doesn't exist before
        assert not pyproject_path.exists()
        
        # Run the function
        ensure_pyproject_toml()
        
        # Verify file exists after
        assert pyproject_path.exists()
        
        # Verify content contains black configuration
        content = pyproject_path.read_text()
        assert "[tool.black]" in content
        assert "line-length = 88" in content
        assert "target-version" in content
        
        # Verify content contains ruff configuration
        assert "[tool.ruff]" in content
        assert "select" in content
        assert "E" in content  # pycodestyle errors
        assert "F" in content  # pyflakes

    def test_pyproject_toml_idempotent(self, temp_project_root):
        """Test that running ensure_pyproject_toml twice doesn't break anything."""
        pyproject_path = temp_project_root / "pyproject.toml"
        
        # Run twice
        ensure_pyproject_toml()
        ensure_pyproject_toml()
        
        # Verify file still exists and is valid
        assert pyproject_path.exists()
        content = pyproject_path.read_text()
        assert "[tool.black]" in content
        assert "[tool.ruff]" in content

    def test_ruff_config_creation(self, temp_project_root):
        """Test that .ruff.toml is created when not in pyproject.toml."""
        # First, create a minimal pyproject.toml without ruff config
        pyproject_path = temp_project_root / "pyproject.toml"
        pyproject_path.write_text("[tool.black]\nline-length = 88\n")
        
        ruff_toml_path = temp_project_root / ".ruff.toml"
        
        # Verify .ruff.toml doesn't exist before
        assert not ruff_toml_path.exists()
        
        # Run the function
        ensure_ruff_config()
        
        # Verify file exists after
        assert ruff_toml_path.exists()
        
        # Verify content
        content = ruff_toml_path.read_text()
        assert "[lint]" in content
        assert "select" in content
        assert "E" in content
        assert "F" in content

    def test_ruff_config_skipped_when_in_pyproject(self, temp_project_root):
        """Test that .ruff.toml is not created if ruff config exists in pyproject.toml."""
        pyproject_path = temp_project_root / "pyproject.toml"
        pyproject_path.write_text("[tool.black]\n[tool.ruff]\nselect = [\"E\"]\n")
        
        ruff_toml_path = temp_project_root / ".ruff.toml"
        
        # Run the function
        ensure_ruff_config()
        
        # Verify .ruff.toml was NOT created
        assert not ruff_toml_path.exists()

    def test_flake8_config_creation(self, temp_project_root):
        """Test that .flake8 is created with correct content."""
        flake8_path = temp_project_root / ".flake8"
        
        # Verify file doesn't exist before
        assert not flake8_path.exists()
        
        # Run the function
        ensure_flake8_config()
        
        # Verify file exists after
        assert flake8_path.exists()
        
        # Verify content
        content = flake8_path.read_text()
        assert "[flake8]" in content
        assert "max-line-length = 88" in content
        assert "ignore" in content

    def test_flake8_config_idempotent(self, temp_project_root):
        """Test that running ensure_flake8_config twice doesn't break anything."""
        flake8_path = temp_project_root / ".flake8"
        
        # Run twice
        ensure_flake8_config()
        ensure_flake8_config()
        
        # Verify file still exists and is valid
        assert flake8_path.exists()
        content = flake8_path.read_text()
        assert "[flake8]" in content
        assert "max-line-length = 88" in content

    def test_all_config_files_created(self, temp_project_root):
        """Test that all three configuration files are created by the main flow."""
        # Run the individual functions
        ensure_pyproject_toml()
        ensure_ruff_config()
        ensure_flake8_config()
        
        # Verify all files exist
        assert (temp_project_root / "pyproject.toml").exists()
        assert (temp_project_root / ".ruff.toml").exists() or "[tool.ruff]" in (temp_project_root / "pyproject.toml").read_text()
        assert (temp_project_root / ".flake8").exists()

    def test_config_files_parse_correctly(self, temp_project_root):
        """Test that pyproject.toml can be parsed as valid TOML."""
        ensure_pyproject_toml()
        
        pyproject_path = temp_project_root / "pyproject.toml"
        
        # This will raise an exception if the file is not valid TOML
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        # Verify the structure
        assert "tool" in config
        assert "black" in config["tool"]
        assert "ruff" in config["tool"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])