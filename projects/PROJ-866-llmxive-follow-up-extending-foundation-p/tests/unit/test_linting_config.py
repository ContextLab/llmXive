"""
Unit tests for linting configuration setup.
"""
import os
import tempfile
import pytest
from code.setup_linting import (
    create_linting_config,
    create_formatting_config,
    create_ruffignore,
    create_gitignore_update,
)


class TestLinterConfig:
    """Tests for ruff configuration generation."""

    def test_ruff_toml_created(self, tmp_path):
        """Test that ruff.toml is created with correct content."""
        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_linting_config()
            
            # Check file exists
            assert os.path.exists("code/ruff.toml")
            
            # Check content
            with open("code/ruff.toml", "r") as f:
                content = f.read()
            
            assert "[lint]" in content
            assert 'select = [' in content
            assert '"E"' in content
            assert '"W"' in content
            assert '"F"' in content
            assert "[format]" in content
        finally:
            os.chdir(original_dir)

    def test_ruff_toml_has_black_ignore(self, tmp_path):
        """Test that ruff.toml ignores E501 (line length handled by black)."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_linting_config()
            
            with open("code/ruff.toml", "r") as f:
                content = f.read()
            
            assert "E501" in content
        finally:
            os.chdir(original_dir)


class TestFormatterConfig:
    """Tests for black configuration generation."""

    def test_pyproject_toml_created(self, tmp_path):
        """Test that pyproject.toml is created with black config."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_formatting_config()
            
            assert os.path.exists("pyproject.toml")
            
            with open("pyproject.toml", "r") as f:
                content = f.read()
            
            assert "[tool.black]" in content
            assert "line-length = 88" in content
            assert "target-version" in content
        finally:
            os.chdir(original_dir)

    def test_pyproject_toml_updated(self, tmp_path):
        """Test that existing pyproject.toml is updated correctly."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create a basic pyproject.toml
            with open("pyproject.toml", "w") as f:
                f.write("[project]\nname = 'test'\n")
            
            create_formatting_config()
            
            with open("pyproject.toml", "r") as f:
                content = f.read()
            
            assert "[tool.black]" in content
            assert "line-length = 88" in content
        finally:
            os.chdir(original_dir)

    def test_pyproject_toml_not_duplicated(self, tmp_path):
        """Test that black config is not added twice."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create pyproject.toml with black config
            with open("pyproject.toml", "w") as f:
                f.write("[project]\nname = 'test'\n[tool.black]\nline-length = 88\n")
            
            create_formatting_config()
            
            with open("pyproject.toml", "r") as f:
                content = f.read()
            
            # Count occurrences of [tool.black]
            count = content.count("[tool.black]")
            assert count == 1
        finally:
            os.chdir(original_dir)


class TestIgnoreFiles:
    """Tests for ignore file generation."""

    def test_ruffignore_created(self, tmp_path):
        """Test that .ruffignore is created."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_ruffignore()
            
            assert os.path.exists(".ruffignore")
            
            with open(".ruffignore", "r") as f:
                content = f.read()
            
            assert "__pycache__" in content
            assert ".git" in content
        finally:
            os.chdir(original_dir)

    def test_gitignore_updated(self, tmp_path):
        """Test that .gitignore is updated with ruff cache."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create basic .gitignore
            with open(".gitignore", "w") as f:
                f.write("# Python\n__pycache__/\n")
            
            create_gitignore_update()
            
            with open(".gitignore", "r") as f:
                content = f.read()
            
            assert ".ruff_cache/" in content
        finally:
            os.chdir(original_dir)

    def test_gitignore_created_if_missing(self, tmp_path):
        """Test that .gitignore is created if it doesn't exist."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_gitignore_update()
            
            assert os.path.exists(".gitignore")
            
            with open(".gitignore", "r") as f:
                content = f.read()
            
            assert ".ruff_cache/" in content
        finally:
            os.chdir(original_dir)


class TestIntegration:
    """Integration tests for the full setup process."""

    def test_full_setup(self, tmp_path):
        """Test running all setup functions creates all expected files."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_linting_config()
            create_formatting_config()
            create_ruffignore()
            create_gitignore_update()
            
            # Check all files exist
            assert os.path.exists("code/ruff.toml")
            assert os.path.exists("pyproject.toml")
            assert os.path.exists(".ruffignore")
            assert os.path.exists(".gitignore")
            
            # Verify content integrity
            with open("code/ruff.toml", "r") as f:
                assert "[lint]" in f.read()
            
            with open("pyproject.toml", "r") as f:
                assert "[tool.black]" in f.read()
            
            with open(".ruffignore", "r") as f:
                assert "__pycache__" in f.read()
            
            with open(".gitignore", "r") as f:
                assert ".ruff_cache/" in f.read()
        finally:
            os.chdir(original_dir)