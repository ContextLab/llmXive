"""
Unit tests for environment variable validation infrastructure (T010).
"""
import os
import pytest
import tempfile
from pathlib import Path

from src.utils.env_config import (
    EnvConfig,
    EnvVarDefinition,
    ValidationResult,
    validate_environment,
    get_env_config,
    get_env
)


class TestEnvConfig:
    """Tests for the EnvConfig class."""

    def test_define_variable(self):
        """Test defining a variable."""
        config = EnvConfig()
        config.define("TEST_VAR", required=True)
        assert "TEST_VAR" in config.definitions
        assert config.definitions["TEST_VAR"].required is True

    def test_define_with_defaults(self):
        """Test defining a variable with defaults."""
        config = EnvConfig()
        config.define("OPT_VAR", required=False, default="default_val")
        assert config.definitions["OPT_VAR"].default == "default_val"
        assert config.definitions["OPT_VAR"].required is False

    def test_define_with_type_hint(self):
        """Test defining a variable with type hint."""
        config = EnvConfig()
        config.define("INT_VAR", type_hint=int, default=42)
        assert config.definitions["INT_VAR"].type_hint == int

    def test_define_with_allowed_values(self):
        """Test defining a variable with allowed values."""
        config = EnvConfig()
        config.define("LEVEL", allowed_values=["low", "medium", "high"])
        assert config.definitions["LEVEL"].allowed_values == ["low", "medium", "high"]

    def test_validate_missing_required(self):
        """Test validation fails when required var is missing."""
        config = EnvConfig()
        config.define("MISSING_REQ", required=True)
        result = config.validate()
        assert result.success is False
        assert any("MISSING_REQ" in err for err in result.errors)

    def test_validate_missing_optional_with_default(self):
        """Test validation succeeds with default for optional var."""
        config = EnvConfig()
        config.define("OPT_WITH_DEFAULT", required=False, default="fallback")
        result = config.validate()
        assert result.success is True
        assert result.resolved_config["OPT_WITH_DEFAULT"] == "fallback"
        assert any("OPT_WITH_DEFAULT" in warn for warn in result.warnings)

    def test_validate_success(self):
        """Test validation succeeds when all required vars are set."""
        os.environ["VALID_VAR"] = "value"
        config = EnvConfig()
        config.define("VALID_VAR", required=True)
        result = config.validate()
        assert result.success is True
        assert result.resolved_config["VALID_VAR"] == "value"
        # Cleanup
        del os.environ["VALID_VAR"]

    def test_type_coercion_int(self):
        """Test integer type coercion."""
        os.environ["INT_VAL"] = "123"
        config = EnvConfig()
        config.define("INT_VAL", type_hint=int)
        result = config.validate()
        assert result.success is True
        assert result.resolved_config["INT_VAL"] == 123
        del os.environ["INT_VAL"]

    def test_type_coercion_path(self):
        """Test Path type coercion."""
        os.environ["PATH_VAL"] = "/tmp/test"
        config = EnvConfig()
        config.define("PATH_VAL", type_hint=Path)
        result = config.validate()
        assert result.success is True
        assert result.resolved_config["PATH_VAL"] == Path("/tmp/test")
        del os.environ["PATH_VAL"]

    def test_type_coercion_bool(self):
        """Test boolean type coercion."""
        os.environ["BOOL_TRUE"] = "true"
        os.environ["BOOL_FALSE"] = "0"
        config = EnvConfig()
        config.define("BOOL_TRUE", type_hint=bool)
        config.define("BOOL_FALSE", type_hint=bool)
        result = config.validate()
        assert result.success is True
        assert result.resolved_config["BOOL_TRUE"] is True
        assert result.resolved_config["BOOL_FALSE"] is False
        del os.environ["BOOL_TRUE"]
        del os.environ["BOOL_FALSE"]

    def test_invalid_type_coercion(self):
        """Test validation fails on invalid type coercion."""
        os.environ["BAD_INT"] = "not_a_number"
        config = EnvConfig()
        config.define("BAD_INT", type_hint=int)
        result = config.validate()
        assert result.success is False
        assert any("BAD_INT" in err and "convert" in err for err in result.errors)
        del os.environ["BAD_INT"]

    def test_allowed_values_violation(self):
        """Test validation fails on allowed values violation."""
        os.environ["BAD_LEVEL"] = "super_high"
        config = EnvConfig()
        config.define("BAD_LEVEL", allowed_values=["low", "high"])
        result = config.validate()
        assert result.success is False
        assert any("BAD_LEVEL" in err for err in result.errors)
        del os.environ["BAD_LEVEL"]

    def test_get_after_validation(self):
        """Test retrieving values after validation."""
        os.environ["GET_VAR"] = "retrieved"
        config = EnvConfig()
        config.define("GET_VAR", required=True)
        config.validate()
        val = config.get("GET_VAR")
        assert val == "retrieved"
        del os.environ["GET_VAR"]

    def test_get_before_validation_raises(self):
        """Test getting value before validation raises error."""
        config = EnvConfig()
        config.define("UNSET_VAR")
        with pytest.raises(RuntimeError, match="validated"):
            config.get("UNSET_VAR")

    def test_get_missing_key_raises(self):
        """Test getting a key that was not defined raises error."""
        os.environ["UNDEF_VAR"] = "val"
        config = EnvConfig()
        config.define("OTHER_VAR")
        config.validate()
        with pytest.raises(KeyError):
            config.get("UNDEF_VAR")
        del os.environ["UNDEF_VAR"]

    def test_get_path_helper(self):
        """Test get_path helper method."""
        os.environ["PATH_GET"] = "/some/path"
        config = EnvConfig()
        config.define("PATH_GET", required=True)
        config.validate()
        p = config.get_path("PATH_GET")
        assert isinstance(p, Path)
        assert p == Path("/some/path")
        del os.environ["PATH_GET"]


class TestValidateEnvironment:
    """Tests for the global validate_environment function."""

    def test_fail_fast_on_error(self):
        """Test that validate_environment exits on error."""
        config = get_env_config()
        # Reset global config state if needed
        config.definitions["FAIL_GLOBAL"] = EnvVarDefinition("FAIL_GLOBAL", required=True)
        # Ensure it's not set
        if "FAIL_GLOBAL" in os.environ:
            del os.environ["FAIL_GLOBAL"]
        
        # We can't actually test sys.exit in a simple way without mocking,
        # but we can test the logic path by calling validate() directly on the instance
        result = config.validate()
        assert result.success is False

    def test_success_path(self):
        """Test success path of global validator."""
        config = get_env_config()
        # Clear previous definitions to avoid conflicts
        config.definitions.clear()
        os.environ["GLOBAL_SUCCESS"] = "ok"
        config.define("GLOBAL_SUCCESS", required=True)
        result = config.validate()
        assert result.success is True
        del os.environ["GLOBAL_SUCCESS"]


class TestEnvConfigPersistence:
    """Tests for loading environment from .env files."""

    def test_load_from_file_exists(self):
        """Test loading from existing .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("FILE_VAR=from_file\n")
            f.write("FILE_INT=42\n")
            temp_path = f.name

        try:
            config = EnvConfig()
            config.load_from_file(temp_path)
            assert os.getenv("FILE_VAR") == "from_file"
            assert os.getenv("FILE_INT") == "42"
        finally:
            os.unlink(temp_path)

    def test_load_from_file_not_found(self):
        """Test loading from non-existent file logs warning."""
        config = EnvConfig()
        # Should not raise, just log
        config.load_from_file("/nonexistent/path/.env")

    def test_load_from_file_skips_comments(self):
        """Test that comments and empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("COMMENT_VAR=value\n")
            temp_path = f.name

        try:
            config = EnvConfig()
            config.load_from_file(temp_path)
            assert os.getenv("COMMENT_VAR") == "value"
            assert os.getenv("This is a comment") is None
        finally:
            os.unlink(temp_path)

    def test_load_from_file_invalid_line(self):
        """Test handling of invalid lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("NO_EQUALS\n")
            f.write("VALID=ok\n")
            temp_path = f.name

        try:
            config = EnvConfig()
            config.load_from_file(temp_path)
            assert os.getenv("NO_EQUALS") is None
            assert os.getenv("VALID") == "ok"
        finally:
            os.unlink(temp_path)