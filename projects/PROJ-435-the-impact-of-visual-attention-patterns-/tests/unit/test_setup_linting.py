"""Unit tests for the setup_linting module."""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_linting import get_project_root, run_command, create_ruff_config, create_black_config


class TestSetupLinting:
    """Test cases for setup_linting functions."""

    def test_get_project_root(self):
        """Test that get_project_root returns the correct path."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        # The project root should contain a 'code' directory
        assert (root / "code").exists()

    def test_run_command_success(self):
        """Test run_command with a successful command."""
        # Use a simple command that should always succeed
        result = run_command(["echo", "test"], "Test command")
        assert result is True

    def test_run_command_failure(self):
        """Test run_command with a failing command."""
        # Use a command that should fail
        result = run_command(["false"], "Failing command")
        assert result is False

    def test_create_ruff_config(self):
        """Test that ruff configuration is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a mock pyproject.toml
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text("# Existing content\n")
            
            # Temporarily override get_project_root
            original_func = get_project_root
            import setup_linting
            setup_linting.get_project_root = lambda: tmp_path
            
            try:
                config_path = create_ruff_config()
                assert config_path.exists()
                content = config_path.read_text()
                assert "[tool.ruff]" in content
                assert "select" in content
            finally:
                # Restore original function
                setup_linting.get_project_root = original_func

    def test_create_black_config(self):
        """Test that black configuration is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a mock pyproject.toml
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text("# Existing content\n")
            
            # Temporarily override get_project_root
            original_func = get_project_root
            import setup_linting
            setup_linting.get_project_root = lambda: tmp_path
            
            try:
                config_path = create_black_config()
                assert config_path.exists()
                content = config_path.read_text()
                assert "[tool.black]" in content
                assert "line-length" in content
            finally:
                # Restore original function
                setup_linting.get_project_root = original_func

    def test_config_merging(self):
        """Test that configurations are properly merged with existing content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a pyproject.toml with existing tool configs
            pyproject = tmp_path / "pyproject.toml"
            existing_content = """[tool.mypy]
python_version = 3.11
"""
            pyproject.write_text(existing_content)
            
            # Temporarily override get_project_root
            original_func = get_project_root
            import setup_linting
            setup_linting.get_project_root = lambda: tmp_path
            
            try:
                # Create both configs
                ruff_path = create_ruff_config()
                black_path = create_black_config()
                
                assert ruff_path.exists()
                assert black_path.exists()
                
                content = pyproject.read_text()
                
                # Check that both configs are present
                assert "[tool.ruff]" in content
                assert "[tool.black]" in content
                
                # Check that original content is preserved
                assert "[tool.mypy]" in content
            finally:
                # Restore original function
                setup_linting.get_project_root = original_func