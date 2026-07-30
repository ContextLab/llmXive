import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure we can import from code
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import (
    get_config_value,
    get_int_config,
    get_float_config,
    get_bool_config,
    get_api_key,
    get_data_source_url,
    load_environment,
    initialize_config
)

@pytest.fixture
def mock_env():
    """Fixture to provide a clean environment for testing."""
    with patch.dict(os.environ, {
        'TEST_STRING': 'hello_world',
        'TEST_INT': '42',
        'TEST_FLOAT': '3.14159',
        'TEST_BOOL_TRUE': 'true',
        'TEST_BOOL_FALSE': 'false',
        'TEST_BOOL_ON': 'on',
        'TEST_BOOL_OFF': 'off',
        'MATERIALS_PROJECT_API_KEY': 'mock_key_123',
        'NIST_URL': 'https://nist.example.com'
    }, clear=False):
        yield

def test_get_config_value(mock_env):
    """Test retrieving a string configuration value."""
    assert get_config_value('TEST_STRING') == 'hello_world'
    assert get_config_value('NON_EXISTENT', 'default') == 'default'

def test_get_int_config(mock_env):
    """Test retrieving and parsing integer configuration values."""
    assert get_int_config('TEST_INT') == 42
    assert get_int_config('NON_EXISTENT', 100) == 100
    # Test invalid integer parsing
    with patch.dict(os.environ, {'TEST_BAD_INT': 'abc'}, clear=False):
        assert get_int_config('TEST_BAD_INT', 99) == 99

def test_get_float_config(mock_env):
    """Test retrieving and parsing float configuration values."""
    assert get_float_config('TEST_FLOAT') == 3.14159
    assert get_float_config('NON_EXISTENT', 1.0) == 1.0
    # Test invalid float parsing
    with patch.dict(os.environ, {'TEST_BAD_FLOAT': 'abc'}, clear=False):
        assert get_float_config('TEST_BAD_FLOAT', 2.5) == 2.5

def test_get_bool_config(mock_env):
    """Test retrieving and parsing boolean configuration values."""
    assert get_bool_config('TEST_BOOL_TRUE') is True
    assert get_bool_config('TEST_BOOL_FALSE') is False
    assert get_bool_config('TEST_BOOL_ON') is True
    assert get_bool_config('TEST_BOOL_OFF') is False
    assert get_bool_config('NON_EXISTENT', True) is True
    assert get_bool_config('NON_EXISTENT', False) is False

def test_get_api_key(mock_env):
    """Test retrieving API keys with correct naming convention."""
    assert get_api_key('materials_project') == 'mock_key_123'
    assert get_api_key('non_existent', 'fallback') == 'fallback'

def test_get_data_source_url(mock_env):
    """Test retrieving data source URLs with correct naming convention."""
    assert get_data_source_url('nist') == 'https://nist.example.com'
    assert get_data_source_url('unknown', 'http://default.com') == 'http://default.com'

def test_load_environment_warning(caplog):
    """Test that a warning is logged if .env is missing."""
    with patch('code.config._ENV_PATH', Path('/nonexistent/.env')):
        with patch('code.config._ENV_EXAMPLE_PATH', Path('/existent/.env.example')):
            # Reset cache to force reload
            import code.config
            code.config._config_cache = None
            load_environment()
            assert "not found" in caplog.text
