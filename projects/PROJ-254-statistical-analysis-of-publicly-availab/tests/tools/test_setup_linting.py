"""
Tests for the setup_linting tool.

These tests verify that the configuration files are created correctly.
"""
import os
import tempfile
from pathlib import Path
import shutil
import sys

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.setup_linting import (
    create_pyproject_toml,
    create_ruff_toml,
    ensure_requirements_entry,
)


class TestSetupLinting:
    """Test cases for setup_linting module functions."""

    def test_pyproject_toml_creation(self):
        """Test that pyproject.toml content is generated correctly."""
        content = create_pyproject_toml()
        
        # Check for essential sections
        assert "[build-system]" in content
        assert "[project]" in content
        assert "[tool.black]" in content
        
        # Check for Black settings
        assert "line-length = 88" in content
        assert "target-version = ['py311']" in content
        
        # Check for dependencies
        assert "pandas" in content
        assert "numpy" in content
        assert "gensim" in content

    def test_ruff_toml_creation(self):
        """Test that .ruff.toml content is generated correctly."""
        content = create_ruff_toml()
        
        # Check for essential sections
        assert "[ruff]" in content
        assert "[lint]" in content
        assert "[format]" in content
        
        # Check for Ruff settings
        assert "line-length = 88" in content
        assert "target-version = \"py311\"" in content
        
        # Check for lint rules
        assert 'select = ["E4", "E7", "E9", "F", "I", "N", "UP", "B", "C4", "SIM"]' in content

    def test_requirements_entry_creation(self):
        """Test that requirements.txt is updated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            req_file = tmpdir_path / "requirements.txt"
            
            # Create a basic requirements.txt
            req_file.write_text("pandas\nnumpy\n")
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Test adding new dependencies
                ensure_requirements_entry()
                
                content = req_file.read_text()
                assert "ruff" in content
                assert "black" in content
            finally:
                os.chdir(original_cwd)

    def test_requirements_entry_skip_existing(self):
        """Test that existing dependencies are not duplicated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            req_file = tmpdir_path / "requirements.txt"
            
            # Create requirements.txt with existing ruff and black
            req_file.write_text("pandas\nruff\nblack\n")
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Store original content
                original_content = req_file.read_text()
                
                # Run the function
                ensure_requirements_entry()
                
                # Content should be unchanged
                new_content = req_file.read_text()
                assert original_content == new_content
            finally:
                os.chdir(original_cwd)

    def test_config_files_existence_in_temp(self):
        """Test that configuration files can be created in a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Create requirements.txt first
                req_file = tmpdir_path / "requirements.txt"
                req_file.write_text("pandas\n")
                
                # Create config files
                pyproject_content = create_pyproject_toml()
                pyproject_path = Path("pyproject.toml")
                pyproject_path.write_text(pyproject_content)
                
                ruff_content = create_ruff_toml()
                ruff_path = Path(".ruff.toml")
                ruff_path.write_text(ruff_content)
                
                # Verify files exist
                assert pyproject_path.exists()
                assert ruff_path.exists()
                
                # Verify content is valid
                assert len(pyproject_path.read_text()) > 100
                assert len(ruff_path.read_text()) > 100
            finally:
                os.chdir(original_cwd)