"""
Unit tests for environment configuration management (T011).
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    load_environment,
    initialize_config,
    get_config_value,
    get_int_config,
    get_float_config,
    get_bool_config,
    get_api_key,
    get_data_source_url,
    _manual_load_dotenv
)

class TestConfigLoading:
    """Tests for .env loading and parsing."""

    def test_manual_load_dotenv(self, tmp_path):
        """Test manual parsing of .env file content."""
        env_file = tmp_path / ".env"
        content = """
        # Comment
        KEY1=value1
        KEY2="quoted value"
        KEY3='single quoted'
        KEY4=
        """
        env_file.write_text(content)

        _manual_load_dotenv(env_file)

        assert os.getenv("KEY1") == "value1"
        assert os.getenv("KEY2") == "quoted value"
        assert os.getenv("KEY3") == "single quoted"
        assert os.getenv("KEY4") == ""
        # Comment should not be set
        assert os.getenv("KEY_COMMENT") is None

    def test_load_environment_missing_file(self, monkeypatch):
        """Test behavior when .env file is missing."""
        # Ensure no .env exists in the expected location
        # This test relies on the fact that load_environment handles missing files gracefully
        result = load_environment()
        assert result is True

    def test_initialize_config_defaults(self, monkeypatch):
        """Test that default values are set when env vars are missing."""
        # Clear relevant env vars to force defaults
        for key in ["LOG_LEVEL", "RANDOM_SEED", "DATA_SOURCE"]:
            monkeypatch.delenv(key, raising=False)

        # Re-initialize to clear cache if necessary (simulating fresh start)
        # Note: In a real scenario, we might need to reset the module state
        # For this test, we assume a fresh process or mock the cache
        
        config = initialize_config()
        
        assert config["LOG_LEVEL"] == "INFO"
        assert config["RANDOM_SEED"] == 42
        assert config["DATA_SOURCE"] == "materials_project"

class TestConfigGetters:
    """Tests for configuration getter functions."""

    def setup_method(self):
        """Setup test fixtures."""
        # Reset cache for each test to ensure isolation
        from code import config
        config._config_cache = {}
        config._is_initialized = False
        
        # Set some env vars for testing
        os.environ["TEST_INT"] = "123"
        os.environ["TEST_FLOAT"] = "45.67"
        os.environ["TEST_BOOL_TRUE"] = "true"
        os.environ["TEST_BOOL_FALSE"] = "false"
        os.environ["TEST_BOOL_YES"] = "yes"
        os.environ["TEST_BOOL_ON"] = "on"
        os.environ["TEST_BOOL_1"] = "1"
        os.environ["TEST_API_KEY"] = "secret123"

    def teardown_method(self):
        """Cleanup env vars after test."""
        from code import config
        config._config_cache = {}
        config._is_initialized = False
        
        keys = ["TEST_INT", "TEST_FLOAT", "TEST_BOOL_TRUE", "TEST_BOOL_FALSE", 
                "TEST_BOOL_YES", "TEST_BOOL_ON", "TEST_BOOL_1", "TEST_API_KEY"]
        for k in keys:
            if k in os.environ:
                del os.environ[k]

    def test_get_int_config(self):
        """Test integer configuration retrieval."""
        assert get_int_config("TEST_INT") == 123
        assert get_int_config("NONEXISTENT", 999) == 999
        assert get_int_config("INVALID_INT", 0) == 0

    def test_get_float_config(self):
        """Test float configuration retrieval."""
        assert get_float_config("TEST_FLOAT") == 45.67
        assert get_float_config("NONEXISTENT", 1.0) == 1.0

    def test_get_bool_config(self):
        """Test boolean configuration retrieval."""
        assert get_bool_config("TEST_BOOL_TRUE") is True
        assert get_bool_config("TEST_BOOL_FALSE") is False
        assert get_bool_config("TEST_BOOL_YES") is True
        assert get_bool_config("TEST_BOOL_ON") is True
        assert get_bool_config("TEST_BOOL_1") is True
        assert get_bool_config("NONEXISTENT", True) is True

    def test_get_api_key(self):
        """Test API key retrieval."""
        # Map TEST_API_KEY to a service name
        # We need to test the mapping logic
        # Since get_api_key looks for specific env var names, we mock the env var
        os.environ["API_KEY_MATERIALS_PROJECT"] = "mp_secret"
        
        key = get_api_key("materials_project")
        assert key == "mp_secret"
        
        key = get_api_key("mp")
        assert key == "mp_secret"
        
        key = get_api_key("unknown_service")
        assert key == ""

    def test_get_data_source_url(self):
        """Test data source URL retrieval."""
        os.environ["DATA_SOURCE"] = "nist"
        url = get_data_source_url()
        assert "nist" in url

        os.environ["DATA_SOURCE"] = "materials_project"
        url = get_data_source_url()
        assert "materialsproject.org" in url