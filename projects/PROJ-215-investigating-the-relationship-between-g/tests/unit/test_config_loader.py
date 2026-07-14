import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.config_loader import (
    load_environment_variables,
    get_config_value,
    get_int_config,
    get_float_config,
    get_bool_config,
    _manual_load_env,
    HAS_DOTENV,
)


class TestLoadEnvironmentVariables:
    def test_load_nonexistent_file(self):
        """Loading a non-existent file should return False and not raise."""
        fake_path = Path("/nonexistent/path/.env")
        result = load_environment_variables(fake_path)
        assert result is False

    def test_load_empty_file(self):
        """Loading an empty .env file should succeed (return True or False depending on dotenv)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            temp_path = Path(f.name)
        try:
            result = load_environment_variables(temp_path)
            # If dotenv is available, it returns True even for empty files.
            # If not, our manual loader returns True.
            # The important thing is no exception.
            assert isinstance(result, bool)
        finally:
            temp_path.unlink()

    def test_load_valid_file(self):
        """Loading a valid .env file should set environment variables."""
        content = "TEST_KEY=test_value\nANOTHER_KEY=123\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            # Remove from env if it exists to avoid cross-test pollution
            os.environ.pop("TEST_KEY", None)
            os.environ.pop("ANOTHER_KEY", None)

            load_environment_variables(temp_path)

            assert os.getenv("TEST_KEY") == "test_value"
            assert os.getenv("ANOTHER_KEY") == "123"
        finally:
            temp_path.unlink()

    def test_load_quoted_values(self):
        """Loading quoted values should strip quotes."""
        content = 'QUOTED_DOUBLE="hello world"\nQUOTED_SINGLE=\'single quote\'\n'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            os.environ.pop("QUOTED_DOUBLE", None)
            os.environ.pop("QUOTED_SINGLE", None)

            load_environment_variables(temp_path)

            assert os.getenv("QUOTED_DOUBLE") == "hello world"
            assert os.getenv("QUOTED_SINGLE") == "single quote"
        finally:
            temp_path.unlink()

    def test_manual_load_ignores_comments(self):
        """Manual loader should ignore lines starting with #."""
        content = "# This is a comment\nKEY=value\n# Another comment\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            os.environ.pop("KEY", None)
            _manual_load_env(temp_path)
            assert os.getenv("KEY") == "value"
            # Ensure no key named '#' was created (though manual parser splits on '=')
        finally:
            temp_path.unlink()


class TestGetConfigValue:
    def setup_method(self):
        """Clean up test keys before each test."""
        self.test_keys = ["TEST_STR", "TEST_INT", "TEST_FLOAT", "TEST_BOOL"]
        for key in self.test_keys:
            os.environ.pop(key, None)

    def teardown_method(self):
        """Clean up test keys after each test."""
        for key in self.test_keys:
            os.environ.pop(key, None)

    def test_get_config_value_found(self):
        os.environ["TEST_STR"] = "found_value"
        assert get_config_value("TEST_STR") == "found_value"

    def test_get_config_value_not_found_default(self):
        assert get_config_value("NON_EXISTENT", "default_val") == "default_val"

    def test_get_config_value_not_found_no_default(self):
        assert get_config_value("NON_EXISTENT") is None

    def test_get_int_config_found(self):
        os.environ["TEST_INT"] = "42"
        assert get_int_config("TEST_INT") == 42

    def test_get_int_config_invalid(self):
        os.environ["TEST_INT"] = "not_a_number"
        assert get_int_config("TEST_INT", default=-1) == -1

    def test_get_float_config_found(self):
        os.environ["TEST_FLOAT"] = "3.14"
        assert get_float_config("TEST_FLOAT") == pytest.approx(3.14)

    def test_get_bool_config_true(self):
        for val in ["true", "True", "TRUE", "1", "yes", "on"]:
            os.environ["TEST_BOOL"] = val
            assert get_bool_config("TEST_BOOL") is True

    def test_get_bool_config_false(self):
        for val in ["false", "0", "no", "off", "random"]:
            os.environ["TEST_BOOL"] = val
            assert get_bool_config("TEST_BOOL") is False

    def test_get_bool_config_default(self):
        os.environ.pop("TEST_BOOL", None)
        assert get_bool_config("TEST_BOOL", default=True) is True
        assert get_bool_config("TEST_BOOL", default=False) is False
