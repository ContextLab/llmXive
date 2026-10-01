"""
Tests for linting and formatting setup.
Verifies that configuration files exist and contain expected content.
"""
import os
import pytest
from pathlib import Path
import toml

class TestLintingConfiguration:
    """Test suite for linting and formatting configuration."""

    def test_flake8_config_exists(self):
        """Test that .flake8 configuration file exists."""
        flake8_path = Path(".flake8")
        assert flake8_path.exists(), ".flake8 file must exist"

    def test_flake8_config_valid(self):
        """Test that .flake8 contains valid configuration."""
        flake8_path = Path(".flake8")
        content = flake8_path.read_text()
        
        # Check for essential flake8 settings
        assert "[flake8]" in content, "Missing [flake8] section"
        assert "max-line-length" in content, "Missing max-line-length setting"
        assert "88" in content, "Default line length should be 88"

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml must exist"

    def test_pyproject_toml_contains_black_config(self):
        """Test that pyproject.toml contains black configuration."""
        pyproject_path = Path("pyproject.toml")
        config = toml.load(pyproject_path)
        
        assert "tool" in config, "Missing [tool] section"
        assert "black" in config["tool"], "Missing [tool.black] section"
        
        black_config = config["tool"]["black"]
        assert "line-length" in black_config, "Missing line-length in black config"
        assert black_config["line-length"] == 88, "Line length should be 88"

    def test_precommit_config_exists(self):
        """Test that .pre-commit-config.yaml exists."""
        precommit_path = Path(".pre-commit-config.yaml")
        assert precommit_path.exists(), ".pre-commit-config.yaml must exist"

    def test_precommit_config_contains_black_hook(self):
        """Test that pre-commit config contains black hook."""
        precommit_path = Path(".pre-commit-config.yaml")
        content = precommit_path.read_text()
        
        assert "black" in content, "Missing black hook in pre-commit config"
        assert "psf/black" in content, "Missing psf/black repository reference"

    def test_precommit_config_contains_flake8_hook(self):
        """Test that pre-commit config contains flake8 hook."""
        precommit_path = Path(".pre-commit-config.yaml")
        content = precommit_path.read_text()
        
        assert "flake8" in content, "Missing flake8 hook in pre-commit config"
        assert "pycqa/flake8" in content, "Missing pycqa/flake8 repository reference"

class TestLintingScript:
    """Test suite for setup_linting.py script."""

    def test_setup_linting_script_exists(self):
        """Test that setup_linting.py exists."""
        script_path = Path("code/setup_linting.py")
        assert script_path.exists(), "code/setup_linting.py must exist"

    def test_setup_linting_script_has_main(self):
        """Test that setup_linting.py has a main function."""
        script_path = Path("code/setup_linting.py")
        content = script_path.read_text()
        
        assert "def main():" in content, "Missing main function"
        assert "if __name__" in content, "Missing main execution block"

    def test_setup_linting_script_imports(self):
        """Test that setup_linting.py imports necessary modules."""
        script_path = Path("code/setup_linting.py")
        content = script_path.read_text()
        
        assert "import subprocess" in content, "Missing subprocess import"
        assert "import toml" in content, "Missing toml import"
        assert "from pathlib import Path" in content, "Missing Path import"