"""
Unit tests for configuration management utilities.
"""
import os
import pytest
from pathlib import Path

from utils.config import Config, load_environment, get_env, get_config


class TestConfig:
    """Tests for the Config class."""

    def test_config_get(self):
        """Test getting values from Config."""
        config_dict = {'key1': 'value1', 'key2': 42, 'key3': True}
        config = Config(config_dict)

        assert config.get('key1') == 'value1'
        assert config.get('key2') == 42
        assert config.get('key3') is True
        assert config.get('missing_key') is None
        assert config.get('missing_key', 'default') == 'default'

    def test_config_get_int(self):
        """Test getting integer values from Config."""
        config_dict = {'int_key': '42', 'invalid_int': 'not_a_number'}
        config = Config(config_dict)

        assert config.get_int('int_key') == 42
        assert config.get_int('invalid_int') == 0
        assert config.get_int('missing_key', 10) == 10

    def test_config_get_bool(self):
        """Test getting boolean values from Config."""
        config_dict = {
            'true_str': 'true',
            'false_str': 'false',
            'true_num': '1',
            'false_num': '0',
            'bool_true': True,
            'bool_false': False
        }
        config = Config(config_dict)

        assert config.get_bool('true_str') is True
        assert config.get_bool('false_str') is False
        assert config.get_bool('true_num') is True
        assert config.get_bool('false_num') is False
        assert config.get_bool('bool_true') is True
        assert config.get_bool('bool_false') is False


class TestLoadEnvironment:
    """Tests for load_environment function."""

    def test_load_environment(self):
        """Test loading environment configuration."""
        config = load_environment()

        assert isinstance(config, Config)
        assert config.get('run_mode') in ['production', 'test']
        assert isinstance(config.get_int('random_seed'), int)
        assert 'RUN_MODE' in config.get('required_vars', [])

    def test_get_env(self):
        """Test getting environment variables."""
        # Test existing variable
        run_mode = get_env('RUN_MODE')
        assert run_mode is not None

        # Test non-existing variable with default
        value = get_env('NON_EXISTING_VAR', 'default')
        assert value == 'default'

        # Test non-existing variable without default
        value = get_env('NON_EXISTING_VAR')
        assert value is None

    def test_get_config(self):
        """Test get_config convenience function."""
        config = get_config()
        assert isinstance(config, Config)