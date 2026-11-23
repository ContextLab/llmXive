"""
Unit tests for the setup_linting.py script configuration validation functions.
These tests verify that the configuration files are created correctly and
that the validation logic works as expected.
"""
import os
import sys
import tempfile
import shutil
import tomllib
import configparser
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_linting import (
    check_file_exists,
    validate_ruff_config,
    validate_pyproject_black,
    validate_flake8_config,
    create_ruff_config,
    create_black_config,
    create_flake8_config,
    PROJECT_ROOT,
    PYPROJECT_PATH,
    FLAKE8_PATH,
    RUFF_PATH,
)

class TestSetupLinting:
    """Test suite for setup_linting.py functions."""

    def setup_method(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_root = PROJECT_ROOT
        
        # Mock PROJECT_ROOT to point to temp directory
        import setup_linting
        setup_linting.PROJECT_ROOT = Path(self.temp_dir)
        setup_linting.PYPROJECT_PATH = Path(self.temp_dir) / "pyproject.toml"
        setup_linting.FLAKE8_PATH = Path(self.temp_dir) / ".flake8"
        setup_linting.RUFF_PATH = Path(self.temp_dir) / ".ruff.toml"

    def teardown_method(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Restore original PROJECT_ROOT
        import setup_linting
        setup_linting.PROJECT_ROOT = self.original_root
        setup_linting.PYPROJECT_PATH = self.original_root / "pyproject.toml"
        setup_linting.FLAKE8_PATH = self.original_root / ".flake8"
        setup_linting.RUFF_PATH = self.original_root / ".ruff.toml"

    def test_check_file_exists_true(self):
        """Test check_file_exists returns True when file exists."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.touch()
        
        result = check_file_exists(test_file, "test file")
        assert result is True

    def test_check_file_exists_false(self):
        """Test check_file_exists returns False when file does not exist."""
        non_existent = Path(self.temp_dir) / "non_existent.txt"
        
        result = check_file_exists(non_existent, "test file")
        assert result is False

    def test_create_ruff_config(self):
        """Test that create_ruff_config creates a valid TOML file."""
        create_ruff_config()
        
        assert RUFF_PATH.exists()
        
        # Verify it's valid TOML
        with open(RUFF_PATH, "rb") as f:
            content = tomllib.load(f)
        
        assert "line-length" in content
        assert content["line-length"] == 100
        assert "select" in content
        assert "E" in content["select"]

    def test_create_black_config(self):
        """Test that create_black_config updates pyproject.toml correctly."""
        create_black_config()
        
        assert PYPROJECT_PATH.exists()
        
        with open(PYPROJECT_PATH, "rb") as f:
            content = tomllib.load(f)
        
        assert "tool" in content
        assert "black" in content["tool"]
        assert content["tool"]["black"]["line-length"] == 100

    def test_create_flake8_config(self):
        """Test that create_flake8_config creates a valid config file."""
        create_flake8_config()
        
        assert FLAKE8_PATH.exists()
        
        config = configparser.ConfigParser()
        config.read(FLAKE8_PATH)
        
        assert "flake8" in config
        assert config["flake8"]["max-line-length"] == "100"

    def test_validate_ruff_config_success(self):
        """Test validate_ruff_config returns True when config exists."""
        create_ruff_config()
        valid, error = validate_ruff_config()
        assert valid is True
        assert error is None

    def test_validate_ruff_config_failure(self):
        """Test validate_ruff_config returns False when config missing."""
        # Ensure no config exists
        if RUFF_PATH.exists():
            RUFF_PATH.unlink()
        if PYPROJECT_PATH.exists():
            PYPROJECT_PATH.unlink()
        
        valid, error = validate_ruff_config()
        assert valid is False
        assert error is not None

    def test_validate_pyproject_black_success(self):
        """Test validate_pyproject_black returns True when config exists."""
        create_black_config()
        valid, error = validate_pyproject_black()
        assert valid is True
        assert error is None

    def test_validate_pyproject_black_failure(self):
        """Test validate_pyproject_black returns False when config missing."""
        if PYPROJECT_PATH.exists():
            PYPROJECT_PATH.unlink()
        
        valid, error = validate_pyproject_black()
        assert valid is False
        assert error is not None

    def test_validate_flake8_config_success(self):
        """Test validate_flake8_config returns True when config exists."""
        create_flake8_config()
        valid, error = validate_flake8_config()
        assert valid is True
        assert error is None

    def test_validate_flake8_config_failure(self):
        """Test validate_flake8_config returns False when config missing."""
        if FLAKE8_PATH.exists():
            FLAKE8_PATH.unlink()
        
        valid, error = validate_flake8_config()
        assert valid is False
        assert error is not None

    def test_config_files_created_in_sequence(self):
        """Test that all three config files can be created in sequence."""
        create_ruff_config()
        create_black_config()
        create_flake8_config()
        
        assert RUFF_PATH.exists()
        assert PYPROJECT_PATH.exists()
        assert FLAKE8_PATH.exists()

    def test_ruff_config_contains_required_keys(self):
        """Test that ruff config contains all required configuration keys."""
        create_ruff_config()
        
        with open(RUFF_PATH, "rb") as f:
            content = tomllib.load(f)
        
        required_keys = ["line-length", "target-version", "select", "ignore", "exclude"]
        for key in required_keys:
            assert key in content, f"Missing required key: {key}"

    def test_black_config_contains_required_keys(self):
        """Test that black config contains all required configuration keys."""
        create_black_config()
        
        with open(PYPROJECT_PATH, "rb") as f:
            content = tomllib.load(f)
        
        black_config = content["tool"]["black"]
        required_keys = ["line-length", "target-version", "include", "exclude"]
        for key in required_keys:
            assert key in black_config, f"Missing required key: {key}"

    def test_flake8_config_contains_required_keys(self):
        """Test that flake8 config contains all required configuration keys."""
        create_flake8_config()
        
        config = configparser.ConfigParser()
        config.read(FLAKE8_PATH)
        
        required_keys = ["max-line-length", "exclude", "ignore"]
        for key in required_keys:
            assert key in config["flake8"], f"Missing required key: {key}"
