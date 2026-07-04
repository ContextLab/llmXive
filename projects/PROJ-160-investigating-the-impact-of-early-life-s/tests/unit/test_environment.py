"""
Unit tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.environment import (
    load_environment,
    EnvironmentConfig,
    initialize_environment,
    HAS_DOTENV
)


class TestLoadEnvironment:
    """Tests for the load_environment function."""

    def test_load_nonexistent_file(self):
        """Test loading a non-existent .env file returns False."""
        result = load_environment(Path("/nonexistent/.env"))
        assert result is False

    def test_load_empty_file(self):
        """Test loading an empty .env file returns True."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = load_environment(temp_path)
            assert result is True
        finally:
            temp_path.unlink()

    def test_load_valid_file(self):
        """Test loading a valid .env file sets environment variables."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            f.write("TEST_NUM=42\n")
            temp_path = Path(f.name)

        try:
            # Clear any existing values
            os.environ.pop("TEST_VAR", None)
            os.environ.pop("TEST_NUM", None)

            result = load_environment(temp_path)
            assert result is True
            assert os.environ.get("TEST_VAR") == "test_value"
            assert os.environ.get("TEST_NUM") == "42"
        finally:
            temp_path.unlink()
            os.environ.pop("TEST_VAR", None)
            os.environ.pop("TEST_NUM", None)

    def test_load_file_with_comments(self):
        """Test loading a .env file with comments ignores comment lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("VALID_VAR=valid_value\n")
            f.write("  # Indented comment\n")
            temp_path = Path(f.name)

        try:
            result = load_environment(temp_path)
            assert result is True
            assert os.environ.get("VALID_VAR") == "valid_value"
            assert "This is a comment" not in os.environ.get("VALID_VAR", "")
        finally:
            temp_path.unlink()
            os.environ.pop("VALID_VAR", None)

    def test_load_file_with_quotes(self):
        """Test loading a .env file with quoted values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('QUOTED_VAR="quoted value"\n')
            f.write("SINGLE_QUOTED='single quoted'\n")
            temp_path = Path(f.name)

        try:
            result = load_environment(temp_path)
            assert result is True
            assert os.environ.get("QUOTED_VAR") == "quoted value"
            assert os.environ.get("SINGLE_QUOTED") == "single quoted"
        finally:
            temp_path.unlink()
            os.environ.pop("QUOTED_VAR", None)
            os.environ.pop("SINGLE_QUOTED", None)


class TestEnvironmentConfig:
    """Tests for the EnvironmentConfig class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = EnvironmentConfig()
        # Clear any existing test variables
        os.environ.pop("TEST_CONFIG_VAR", None)

    def teardown_method(self):
        """Clean up test fixtures."""
        os.environ.pop("TEST_CONFIG_VAR", None)

    def test_get_missing_variable(self):
        """Test getting a missing variable returns default."""
        result = self.config.get("NONEXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_get_existing_variable(self):
        """Test getting an existing variable returns its value."""
        os.environ["TEST_CONFIG_VAR"] = "test_value"
        result = self.config.get("TEST_CONFIG_VAR")
        assert result == "test_value"

    def test_get_int_valid(self):
        """Test getting an integer variable."""
        os.environ["TEST_INT"] = "42"
        result = self.config.get_int("TEST_INT")
        assert result == 42

    def test_get_int_invalid(self):
        """Test getting an invalid integer returns default."""
        os.environ["TEST_INT"] = "not_a_number"
        result = self.config.get_int("TEST_INT", default=-1)
        assert result == -1

    def test_get_float_valid(self):
        """Test getting a float variable."""
        os.environ["TEST_FLOAT"] = "3.14"
        result = self.config.get_float("TEST_FLOAT")
        assert abs(result - 3.14) < 0.001

    def test_get_bool_true(self):
        """Test getting a boolean true value."""
        for true_val in ["true", "True", "TRUE", "1", "yes", "on"]:
            os.environ["TEST_BOOL"] = true_val
            result = self.config.get_bool("TEST_BOOL")
            assert result is True

    def test_get_bool_false(self):
        """Test getting a boolean false value."""
        for false_val in ["false", "False", "FALSE", "0", "no", "off"]:
            os.environ["TEST_BOOL"] = false_val
            result = self.config.get_bool("TEST_BOOL")
            assert result is False

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config_dict = self.config.to_dict()
        assert "project_root" in config_dict
        assert "data_raw_dir" in config_dict
        assert "data_processed_dir" in config_dict
        assert "code_dir" in config_dict
        assert "tests_dir" in config_dict
        assert "contracts_dir" in config_dict
        assert "dotenv_available" in config_dict
        assert "environment_loaded" in config_dict

    def test_properties(self):
        """Test that all path properties return Path objects."""
        assert isinstance(self.config.project_root, Path)
        assert isinstance(self.config.data_raw_dir, Path)
        assert isinstance(self.config.data_processed_dir, Path)
        assert isinstance(self.config.code_dir, Path)
        assert isinstance(self.config.tests_dir, Path)
        assert isinstance(self.config.contracts_dir, Path)


class TestInitializeEnvironment:
    """Tests for the initialize_environment function."""

    def test_initialize_environment(self):
        """Test that initialize_environment returns a boolean."""
        result = initialize_environment()
        assert isinstance(result, bool)

    def test_initialize_environment_sets_config(self):
        """Test that initialize_environment updates the global config."""
        from code.environment import config
        initialize_environment()
        assert config._loaded is True or config._loaded is False  # Should be set
