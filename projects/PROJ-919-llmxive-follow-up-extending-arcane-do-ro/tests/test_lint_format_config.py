"""
Unit tests to verify that linting and formatting configurations are present and valid.
This satisfies the requirement for T003: Configure linting (ruff) and formatting (black).
"""
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestLintingConfig:
    """Tests for ruff configuration."""

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists at project root."""
        assert Path("pyproject.toml").exists(), "pyproject.toml must exist"

    def test_ruff_config_exists(self):
        """Verify .ruff.toml or [tool.ruff] in pyproject.toml exists."""
        has_ruff_toml = Path(".ruff.toml").exists()
        has_ruff_in_pyproject = False
        
        if Path("pyproject.toml").exists():
            content = Path("pyproject.toml").read_text()
            if "[tool.ruff]" in content:
                has_ruff_in_pyproject = True
        
        assert has_ruff_toml or has_ruff_in_pyproject, "Ruff configuration must exist"

    def test_ruff_config_valid(self):
        """Verify ruff can parse the configuration without errors."""
        # Try to run ruff check with --config to verify syntax
        result = subprocess.run(
            ["python", "-m", "ruff", "check", "--show-settings", "."],
            capture_output=True,
            text=True,
            timeout=30
        )
        # If ruff is not installed, skip the test (it will be installed via requirements)
        if "No module named 'ruff'" in result.stderr:
            pytest.skip("ruff not installed")
        
        # Configuration errors usually appear in stderr but might not be fatal
        # We primarily check that it doesn't crash with a syntax error
        assert "Invalid" not in result.stderr or "configuration" not in result.stderr.lower(), \
            f"Ruff configuration error: {result.stderr}"


class TestFormattingConfig:
    """Tests for black configuration."""

    def test_black_config_exists(self):
        """Verify black configuration exists in pyproject.toml or .black.toml."""
        has_black_toml = Path(".black.toml").exists()
        has_black_in_pyproject = False
        
        if Path("pyproject.toml").exists():
            content = Path("pyproject.toml").read_text()
            if "[tool.black]" in content:
                has_black_in_pyproject = True
        
        assert has_black_toml or has_black_in_pyproject, "Black configuration must exist"

    def test_black_config_valid(self):
        """Verify black can parse the configuration without errors."""
        result = subprocess.run(
            ["python", "-m", "black", "--check", "--config", "pyproject.toml", "--diff", "."],
            capture_output=True,
            text=True,
            timeout=30
        )
        # If black is not installed, skip the test
        if "No module named 'black'" in result.stderr:
            pytest.skip("black not installed")
        
        # Configuration errors are fatal
        assert "Invalid" not in result.stderr or "configuration" not in result.stderr.lower(), \
            f"Black configuration error: {result.stderr}"

    def test_ruff_and_black_compatible(self):
        """Verify ruff and black are configured to be compatible (e.g., same line length)."""
        pyproject_content = Path("pyproject.toml").read_text()
        
        # Extract line-length from black section
        black_line_length = None
        ruff_line_length = None
        
        in_black_section = False
        in_ruff_section = False
        
        for line in pyproject_content.splitlines():
            if "[tool.black]" in line:
                in_black_section = True
                in_ruff_section = False
                continue
            if "[tool.ruff]" in line:
                in_ruff_section = True
                in_black_section = False
                continue
            if line.strip().startswith("[tool."):
                in_black_section = False
                in_ruff_section = False
                continue
            
            if in_black_section and "line-length" in line:
                try:
                    black_line_length = int(line.split("=")[1].strip())
                except (ValueError, IndexError):
                    pass
            
            if in_ruff_section and "line-length" in line:
                try:
                    ruff_line_length = int(line.split("=")[1].strip())
                except (ValueError, IndexError):
                    pass
        
        # If both are configured, they should match
        if black_line_length is not None and ruff_line_length is not None:
            assert black_line_length == ruff_line_length, \
                f"Black line-length ({black_line_length}) must match ruff line-length ({ruff_line_length})"

class TestDevDependencies:
    """Tests for development dependencies."""

    def test_requirements_includes_dev_tools(self):
        """Verify requirements.txt includes ruff and black."""
        req_path = Path("requirements.txt")
        if not req_path.exists():
            pytest.skip("requirements.txt not found")
        
        content = req_path.read_text().lower()
        assert "ruff" in content, "ruff must be in requirements.txt"
        assert "black" in content, "black must be in requirements.txt"