"""
Tests to verify linting and formatting configuration.
These tests ensure that the configuration files exist and contain
the expected settings.
"""

import os
import sys
import json
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

class TestLintingConfiguration:
    """Test suite for linting and formatting configuration files."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).resolve().parent.parent

    @pytest.fixture
    def code_dir(self):
        """Get the code directory."""
        return Path(__file__).resolve().parent.parent / "code"

    def test_ruff_config_exists(self, code_dir):
        """Test that .ruff.toml configuration file exists."""
        ruff_path = code_dir / ".ruff.toml"
        assert ruff_path.exists(), "Ruff configuration file (.ruff.toml) not found"

    def test_black_config_exists(self, code_dir):
        """Test that .black.toml configuration file exists."""
        black_path = code_dir / ".black.toml"
        assert black_path.exists(), "Black configuration file (.black.toml) not found"

    def test_pre_commit_config_exists(self, code_dir):
        """Test that .pre-commit-config.yaml file exists."""
        pre_commit_path = code_dir / ".pre-commit-config.yaml"
        assert pre_commit_path.exists(), "Pre-commit configuration file not found"

    def test_ruff_config_content(self, code_dir):
        """Test that ruff configuration contains expected settings."""
        ruff_path = code_dir / ".ruff.toml"
        content = ruff_path.read_text()

        # Check for essential linting rules
        assert "E" in content or "pycodestyle" in content, "Ruff config missing pycodestyle rules"
        assert "F" in content or "Pyflakes" in content, "Ruff config missing Pyflakes rules"
        assert "B" in content or "bugbear" in content, "Ruff config missing bugbear rules"

        # Check for line length exclusion (handled by black)
        assert "E501" in content, "Ruff config should ignore E501 (line length) for black"

    def test_black_config_content(self, code_dir):
        """Test that black configuration contains expected settings."""
        black_path = code_dir / ".black.toml"
        content = black_path.read_text()

        # Check for line length setting
        assert "line-length" in content, "Black config should specify line length"
        assert "88" in content, "Black config should use standard 88 character line length"

        # Check for Python version targets
        assert "py3" in content.lower(), "Black config should specify Python version targets"

    def test_pre_commit_hooks(self, code_dir):
        """Test that pre-commit configuration includes black and ruff hooks."""
        pre_commit_path = code_dir / ".pre-commit-config.yaml"
        content = pre_commit_path.read_text()

        assert "black" in content, "Pre-commit config should include black hook"
        assert "ruff" in content, "Pre-commit config should include ruff hook"
        assert "https://github.com/psf/black" in content, "Pre-commit config should reference black repo"
        assert "https://github.com/astral-sh/ruff-pre-commit" in content, "Pre-commit config should reference ruff repo"

    def test_scripts_exist(self, code_dir):
        """Test that linting setup and run scripts exist."""
        scripts_dir = code_dir / "scripts"

        setup_script = scripts_dir / "setup_linting.py"
        run_script = scripts_dir / "run_linting.py"

        assert setup_script.exists(), "Linting setup script not found"
        assert run_script.exists(), "Linting run script not found"

    def test_setup_script_is_executable(self, code_dir):
        """Test that the setup script can be imported without errors."""
        setup_script = code_dir / "scripts" / "setup_linting.py"

        # Try to import the script's main function
        spec = __import__("importlib.util").util.spec_from_file_location(
            "setup_linting", setup_script
        )
        module = __import__("importlib.util").util.module_from_spec(spec)

        # This should not raise an exception if the script is syntactically correct
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"Setup script failed to load: {e}")

        # Check that main function exists
        assert hasattr(module, "main"), "Setup script should have a main function"

    def test_run_script_is_executable(self, code_dir):
        """Test that the run script can be imported without errors."""
        run_script = code_dir / "scripts" / "run_linting.py"

        # Try to import the script's main function
        spec = __import__("importlib.util").util.spec_from_file_location(
            "run_linting", run_script
        )
        module = __import__("importlib.util").util.module_from_spec(spec)

        # This should not raise an exception if the script is syntactically correct
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"Run script failed to load: {e}")

        # Check that main function exists
        assert hasattr(module, "main"), "Run script should have a main function"

    def test_config_files_are_valid_toml(self, code_dir):
        """Test that configuration files are valid TOML (if tomllib is available)."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                pytest.skip("tomllib or tomli not available for TOML validation")

        ruff_path = code_dir / ".ruff.toml"
        black_path = code_dir / ".black.toml"

        # Validate ruff config
        with open(ruff_path, "rb") as f:
            try:
                tomllib.load(f)
            except Exception as e:
                pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

        # Validate black config
        with open(black_path, "rb") as f:
            try:
                tomllib.load(f)
            except Exception as e:
                pytest.fail(f"Invalid TOML in .black.toml: {e}")

    def test_pre_commit_config_is_valid_yaml(self, code_dir):
        """Test that pre-commit configuration is valid YAML."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not available for YAML validation")

        pre_commit_path = code_dir / ".pre-commit-config.yaml"

        with open(pre_commit_path, "r") as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")
