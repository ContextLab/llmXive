"""
Unit tests for the linting setup configuration and verification.
Tests T003: Configure linting and formatting tools (ruff, black).
"""
import os
import sys
import pytest
from pathlib import Path
import json

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_linting import (
    run_command,
    check_tool_availability,
    check_config_file,
    run_lint_check,
    run_format_check
)

class TestLintingSetup:
    """Tests for the linting setup module."""

    def test_check_config_file_exists(self):
        """Test that existing config files are detected."""
        # Create a temporary file to test
        temp_file = Path(__file__).parent / "temp_test_config.toml"
        temp_file.touch()
        
        assert check_config_file(str(temp_file)) is True
        
        # Cleanup
        temp_file.unlink()

    def test_check_config_file_missing(self):
        """Test that missing config files are detected."""
        assert check_config_file("non_existent_file_12345.toml") is False

    def test_run_command_success(self):
        """Test run_command with a simple echo command."""
        return_code, stdout, stderr = run_command(["echo", "hello"])
        assert return_code == 0
        assert "hello" in stdout

    def test_run_command_failure(self):
        """Test run_command with a command that should fail."""
        return_code, stdout, stderr = run_command(["ls", "non_existent_dir_12345"])
        assert return_code != 0

    def test_config_files_exist(self):
        """Verify that the required configuration files exist in the project root."""
        project_root = Path(__file__).parent.parent.parent
        required_configs = [
            "pyproject.toml",
            ".ruff.toml",
            ".black.toml"
        ]
        
        for config in required_configs:
            config_path = project_root / config
            assert config_path.exists(), f"Configuration file {config} is missing"
            assert config_path.is_file(), f"Configuration file {config} is not a file"

    def test_pyproject_toml_content(self):
        """Verify pyproject.toml contains ruff and black configuration."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        assert pyproject_path.exists()
        
        content = pyproject_path.read_text()
        
        # Check for black configuration
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
        assert "line-length" in content, "Black line-length configuration missing"
        
        # Check for ruff configuration
        assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
        assert "select" in content, "Ruff select configuration missing"

    def test_ruff_config_content(self):
        """Verify .ruff.toml contains valid configuration."""
        project_root = Path(__file__).parent.parent.parent
        ruff_path = project_root / ".ruff.toml"
        
        assert ruff_path.exists()
        
        content = ruff_path.read_text()
        assert "line-length" in content
        assert "select" in content

    def test_black_config_content(self):
        """Verify .black.toml contains valid configuration."""
        project_root = Path(__file__).parent.parent.parent
        black_path = project_root / ".black.toml"
        
        assert black_path.exists()
        
        content = black_path.read_text()
        assert "line-length" in content
        assert "target-version" in content

    @pytest.mark.skipif(not check_tool_availability("ruff"), reason="Ruff not installed")
    def test_run_lint_check_structure(self):
        """Test that the lint check function returns expected structure."""
        success, message = run_lint_check()
        
        assert isinstance(success, bool)
        assert isinstance(message, str)
        # The message should not be empty
        assert len(message) > 0

    @pytest.mark.skipif(not check_tool_availability("black"), reason="Black not installed")
    def test_run_format_check_structure(self):
        """Test that the format check function returns expected structure."""
        success, message = run_format_check()
        
        assert isinstance(success, bool)
        assert isinstance(message, str)
        # The message should not be empty
        assert len(message) > 0

    def test_python_files_exist(self):
        """Verify that the setup_linting.py file exists and is valid Python."""
        code_dir = Path(__file__).parent.parent.parent / "code"
        lint_file = code_dir / "setup_linting.py"
        
        assert lint_file.exists()
        
        # Try to compile the file to ensure syntax validity
        with open(lint_file, "r") as f:
            source = f.read()
            try:
                compile(source, str(lint_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in setup_linting.py: {e}")