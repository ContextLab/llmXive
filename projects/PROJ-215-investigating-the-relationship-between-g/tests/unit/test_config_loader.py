import os
import tempfile
from pathlib import Path
import pytest

# We need to mock dotenv if it's not installed, or ensure it is installed.
# For the purpose of these tests, we assume python-dotenv is available.
# If not, the tests that rely on .env loading will be skipped.
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from code.config_loader import (
    load_environment_variables,
    get_config_value,
    get_int_config,
    get_float_config,
    get_bool_config,
    initialize_config,
)


class TestLoadEnvironmentVariables:
    @pytest.mark.skipif(not DOTENV_AVAILABLE, reason="python-dotenv not installed")
    def test_load_from_specific_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("TEST_VAR=hello\nTEST_NUM=42\n")
            
            # Clear from environment first
            os.environ.pop("TEST_VAR", None)
            os.environ.pop("TEST_NUM", None)
            
            result = load_environment_variables(str(env_file))
            assert result is True
            assert os.getenv("TEST_VAR") == "hello"
            assert os.getenv("TEST_NUM") == "42"

    @pytest.mark.skipif(not DOTENV_AVAILABLE, reason="python-dotenv not installed")
    def test_load_from_default_path(self):
        # This test assumes .env exists in project root, which might not be true in CI
        # We'll just verify it doesn't crash if the file doesn't exist
        result = load_environment_variables()
        assert result is True  # Should return True if file doesn't exist and no error

    def test_load_from_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_environment_variables("/nonexistent/.env")

    @pytest.mark.skipif(DOTENV_AVAILABLE, reason="python-dotenv is installed")
    def test_load_requires_dotenv_if_path_specified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("TEST=1\n")
            
            with pytest.raises(ImportError, match="python-dotenv is required"):
                load_environment_variables(str(env_file))


class TestGetConfigValue:
    def test_get_existing_value(self):
        os.environ["TEST_CONFIG_VAR"] = "test_value"
        assert get_config_value("TEST_CONFIG_VAR") == "test_value"
        os.environ.pop("TEST_CONFIG_VAR")

    def test_get_missing_value_with_default(self):
        os.environ.pop("MISSING_CONFIG_VAR", None)
        assert get_config_value("MISSING_CONFIG_VAR", "default_val") == "default_val"

    def test_get_missing_value_without_default(self):
        os.environ.pop("MISSING_CONFIG_VAR", None)
        assert get_config_value("MISSING_CONFIG_VAR") is None


class TestGetIntConfig:
    def test_get_valid_int(self):
        os.environ["TEST_INT"] = "123"
        assert get_int_config("TEST_INT") == 123
        os.environ.pop("TEST_INT")

    def test_get_invalid_int_returns_default(self):
        os.environ["TEST_INVALID_INT"] = "not_a_number"
        assert get_int_config("TEST_INVALID_INT", default=99) == 99
        os.environ.pop("TEST_INVALID_INT")

    def test_get_missing_returns_default(self):
        os.environ.pop("MISSING_INT", None)
        assert get_int_config("MISSING_INT", default=42) == 42


class TestGetFloatConfig:
    def test_get_valid_float(self):
        os.environ["TEST_FLOAT"] = "3.14"
        assert get_float_config("TEST_FLOAT") == 3.14
        os.environ.pop("TEST_FLOAT")

    def test_get_invalid_float_returns_default(self):
        os.environ["TEST_INVALID_FLOAT"] = "not_a_float"
        assert get_float_config("TEST_INVALID_FLOAT", default=2.71) == 2.71
        os.environ.pop("TEST_INVALID_FLOAT")

    def test_get_missing_returns_default(self):
        os.environ.pop("MISSING_FLOAT", None)
        assert get_float_config("MISSING_FLOAT", default=1.0) == 1.0


class TestGetBoolConfig:
    @pytest.mark.parametrize("val,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("Yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("random", False),
    ])
    def test_bool_parsing(self, val, expected):
        os.environ["TEST_BOOL"] = val
        assert get_bool_config("TEST_BOOL") == expected
        os.environ.pop("TEST_BOOL")

    def test_missing_returns_default(self):
        os.environ.pop("MISSING_BOOL", None)
        assert get_bool_config("MISSING_BOOL", default=True) is True


class TestInitializeConfig:
    def test_initialization(self):
        result = initialize_config()
        assert "dotenv_available" in result
        assert "project_root" in result
        assert "output_path" in result
        assert Path(result["project_root"]).is_dir()
        assert Path(result["output_path"]).is_dir()
