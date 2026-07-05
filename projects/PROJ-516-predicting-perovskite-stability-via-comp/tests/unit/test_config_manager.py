"""
Unit tests for configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Adjust import path based on project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.config_manager import load_dotenv_file, get_api_key, ConfigError, validate_environment

class TestConfigManager:
    def test_load_dotenv_file(self, tmp_path):
        """Test loading variables from a .env file."""
        env_content = (
            "KEY1=value1\n"
            "KEY2 = 'value2'\n"
            "KEY3=\"value3\"\n"
            "# Comment\n"
            "\n"
            "KEY4= value4 with spaces "
        )
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)

        load_dotenv_file(env_file)

        assert os.environ.get("KEY1") == "value1"
        assert os.environ.get("KEY2") == "value2"
        assert os.environ.get("KEY3") == "value3"
        assert os.environ.get("KEY4") == "value4 with spaces"

    def test_get_api_key_missing(self):
        """Test that ConfigError is raised when key is missing."""
        # Ensure the variable is not set
        if "TEST_MISSING_KEY" in os.environ:
            del os.environ["TEST_MISSING_KEY"]

        # Temporarily patch the mapping for this test
        import utils.config_manager as cm
        original_vars = cm.env_vars if hasattr(cm, 'env_vars') else {}
        
        # We can't easily patch the internal dict of the function without modifying the module,
        # so we rely on the known mapping for a fake provider or check the error message.
        # Let's test a known provider that we know isn't set.
        with pytest.raises(ConfigError) as exc_info:
            get_api_key("materials_project") # Assuming we didn't set this in the test env
        
        assert "MATERIALS_PROJECT_API_KEY" in str(exc_info.value)

    def test_validate_environment(self):
        """Test the validation function."""
        # This test depends on the current environment state.
        # We just verify it returns a dict with the expected keys.
        results = validate_environment()
        assert isinstance(results, dict)
        assert "materials_project" in results
        assert "nrel" in results
        # Values should be booleans
        assert isinstance(results["materials_project"], bool)
        assert isinstance(results["nrel"], bool)
