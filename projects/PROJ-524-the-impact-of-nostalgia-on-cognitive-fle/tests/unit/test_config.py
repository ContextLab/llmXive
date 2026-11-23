"""
Unit tests for code/config.py configuration management functions.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    get_env_str,
    get_env_int,
    get_env_float,
    get_env_bool,
    get_mmse_threshold,
    get_data_source_url,
    get_log_level
)


class TestEnvGetters:
    def test_get_env_str(self):
        """Test string environment variable retrieval."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = get_env_str('TEST_VAR', 'default')
            assert result == 'test_value'

    def test_get_env_str_default(self):
        """Test string environment variable with default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_str('NONEXISTENT_VAR', 'default_value')
            assert result == 'default_value'

    def test_get_env_int(self):
        """Test integer environment variable retrieval."""
        with patch.dict(os.environ, {'TEST_INT': '42'}):
            result = get_env_int('TEST_INT', 0)
            assert result == 42

    def test_get_env_int_default(self):
        """Test integer environment variable with default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_int('NONEXISTENT_INT', 100)
            assert result == 100

    def test_get_env_float(self):
        """Test float environment variable retrieval."""
        with patch.dict(os.environ, {'TEST_FLOAT': '3.14'}):
            result = get_env_float('TEST_FLOAT', 0.0)
            assert abs(result - 3.14) < 0.001

    def test_get_env_bool_true(self):
        """Test boolean environment variable (true)."""
        with patch.dict(os.environ, {'TEST_BOOL': 'true'}):
            result = get_env_bool('TEST_BOOL', False)
            assert result is True

    def test_get_env_bool_false(self):
        """Test boolean environment variable (false)."""
        with patch.dict(os.environ, {'TEST_BOOL': 'false'}):
            result = get_env_bool('TEST_BOOL', True)
            assert result is False

    def test_get_env_bool_default(self):
        """Test boolean environment variable with default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_bool('NONEXISTENT_BOOL', True)
            assert result is True

class TestSpecificGetters:
    def test_get_mmse_threshold(self):
        """Test MMSE threshold retrieval."""
        with patch.dict(os.environ, {'MMSE_THRESHOLD': '24'}):
            result = get_mmse_threshold()
            assert result == 24

        with patch.dict(os.environ, {}, clear=True):
            result = get_mmse_threshold()
            assert result == 24  # Default

    def test_get_data_source_url(self):
        """Test data source URL retrieval."""
        test_url = 'https://example.com/dataset.csv'
        with patch.dict(os.environ, {'DATA_SOURCE_URL': test_url}):
            result = get_data_source_url()
            assert result == test_url

        with patch.dict(os.environ, {}, clear=True):
            result = get_data_source_url()
            # Should have a default or raise - depends on implementation
            assert result is not None

    def test_get_log_level(self):
        """Test log level retrieval."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            result = get_log_level()
            assert result == 'DEBUG'

        with patch.dict(os.environ, {}, clear=True):
            result = get_log_level()
            assert result == 'INFO'  # Default
