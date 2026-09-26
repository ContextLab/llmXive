"""
Unit tests to verify that linting and formatting configuration files exist and are valid.
"""
import pytest
import os
from pathlib import Path
import tomllib
import sys

# Add the project root to the path to import scripts if needed, 
# though these tests are mostly file-system checks.
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"

class TestLintingSetup:
    """Tests for T002: Configure linting (ruff) and formatting (black) tools."""

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in code/ directory."""
        path = code_dir / "pyproject.toml"
        assert path.exists(), f"{path} does not exist."

    def test_pyproject_toml_valid_syntax(self):
        """Verify pyproject.toml contains valid TOML syntax."""
        path = code_dir / "pyproject.toml"
        try:
            with open(path, "rb") as f:
                tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML syntax in pyproject.toml: {e}")

    def test_pyproject_toml_has_black_config(self):
        """Verify pyproject.toml contains [tool.black] section."""
        path = code_dir / "pyproject.toml"
        with open(path, "rb") as f:
            data = tomllib.load(f)
        
        assert "tool" in data, "Missing [tool] section in pyproject.toml"
        assert "black" in data["tool"], "Missing [tool.black] section in pyproject.toml"
        
        # Check for line-length as a sanity check that it's not empty
        assert "line-length" in data["tool"]["black"], "Missing line-length in [tool.black]"

    def test_pyproject_toml_has_ruff_config(self):
        """Verify pyproject.toml contains [tool.ruff] section."""
        path = code_dir / "pyproject.toml"
        with open(path, "rb") as f:
            data = tomllib.load(f)
        
        assert "tool" in data, "Missing [tool] section in pyproject.toml"
        assert "ruff" in data["tool"], "Missing [tool.ruff] section in pyproject.toml"
        
        # Check for select as a sanity check
        assert "select" in data["tool"]["ruff"], "Missing select in [tool.ruff]"

    def test_ruff_toml_exists(self):
        """Verify .ruff.toml exists in code/ directory."""
        path = code_dir / ".ruff.toml"
        assert path.exists(), f"{path} does not exist."

    def test_ruff_toml_extends_pyproject(self):
        """Verify .ruff.toml extends pyproject.toml."""
        path = code_dir / ".ruff.toml"
        with open(path, "r") as f:
            content = f.read()
        
        assert "extend" in content, "Missing 'extend' key in .ruff.toml"
        assert "pyproject.toml" in content, "Missing 'pyproject.toml' in .ruff.toml extend directive"

    def test_ruff_toml_valid_syntax(self):
        """Verify .ruff.toml is valid TOML (since it's a TOML file)."""
        path = code_dir / ".ruff.toml"
        try:
            with open(path, "rb") as f:
                tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML syntax in .ruff.toml: {e}")