"""
Unit tests for environment variable validation and error handling infrastructure.

Tests cover:
- Loading .env files
- Registering required variables
- Validation logic
- Type casting
- Error handling
"""
import os
import pytest
import tempfile
from pathlib import Path
from src.utils.env_config import (
    EnvConfig,
    EnvValidationError,
    env_config,
    validate_environment
)

class TestEnvConfig:
    """Tests for the EnvConfig class."""
    
    def setup_method(self):
        """Reset environment before each test."""
        # Save original environment
        self.original_env = os.environ.copy()
        # Reset the singleton
        env_config._initialized = False
        env_config.__init__()
    
    def teardown_method(self):
        """Restore environment after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_load_dotenv_creates_variables(self):
        """Test that .env file loading works correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_VAR=value123\n")
            f.write("ANOTHER_VAR=456\n")
            f.write("# This is a comment\n")
            f.write("\n")  # Empty line
            env_path = f.name
        
        try:
            env_config.load_dotenv(env_path)
            assert os.environ.get('TEST_VAR') == 'value123'
            assert os.environ.get('ANOTHER_VAR') == '456'
            assert 'COMMENTS' not in os.environ
        finally:
            os.unlink(env_path)
    
    def test_register_required_variable(self):
        """Test registering a required variable."""
        env_config.register_required('TEST_VAR')
        assert 'TEST_VAR' in env_config._required
    
    def test_validate_missing_required_raises_error(self):
        """Test validation fails for missing required variables."""
        env_config.register_required('MISSING_VAR')
        
        with pytest.raises(EnvValidationError) as exc_info:
            env_config.validate(fail_fast=True)
        
        assert 'MISSING_VAR' in exc_info.value.missing_vars
        assert 'Missing required variables' in str(exc_info.value)
    
    def test_validate_with_default(self):
        """Test that default values are used when variable is missing."""
        env_config.register_required('VAR_WITH_DEFAULT', default='default_value')
        
        result = env_config.validate(fail_fast=True)
        assert result is True
        assert os.environ.get('VAR_WITH_DEFAULT') == 'default_value'
    
    def test_validator_function(self):
        """Test custom validator functions."""
        def is_valid_level(x):
            return x in ['DEBUG', 'INFO', 'ERROR']
        
        env_config.register_required(
            'LOG_LEVEL',
            validator=is_valid_level
        )
        
        # Test with invalid value
        os.environ['LOG_LEVEL'] = 'INVALID'
        result = env_config.validate(fail_fast=False)
        assert result is False
        
        # Test with valid value
        os.environ['LOG_LEVEL'] = 'INFO'
        result = env_config.validate(fail_fast=True)
        assert result is True
    
    def test_get_with_casting(self):
        """Test getting values with type casting."""
        os.environ['TEST_INT'] = '42'
        os.environ['TEST_FLOAT'] = '3.14'
        os.environ['TEST_BOOL'] = 'true'
        os.environ['TEST_STR'] = 'hello'
        
        assert env_config.get('TEST_INT', int) == 42
        assert env_config.get('TEST_FLOAT', float) == 3.14
        assert env_config.get('TEST_BOOL', bool) is True
        assert env_config.get('TEST_STR', str) == 'hello'
    
    def test_get_missing_variable_raises_keyerror(self):
        """Test that missing variable raises KeyError."""
        with pytest.raises(KeyError):
            env_config.get('NON_EXISTENT_VAR')
    
    def test_get_optional_with_default(self):
        """Test optional variable with default."""
        result = env_config.get_optional('MISSING_VAR', default='fallback')
        assert result == 'fallback'
    
    def test_get_optional_type_casting(self):
        """Test optional variable with type casting."""
        os.environ['OPT_INT'] = '100'
        
        result = env_config.get_optional('OPT_INT', default=0, cast_type=int)
        assert result == 100
        
        result = env_config.get_optional('MISSING_INT', default=42, cast_type=int)
        assert result == 42
    
    def test_invalid_cast_falls_back_to_default(self):
        """Test that invalid casting falls back to default."""
        os.environ['BAD_INT'] = 'not_a_number'
        
        result = env_config.get_optional('BAD_INT', default=99, cast_type=int)
        assert result == 99
    
    def test_singleton_pattern(self):
        """Test that EnvConfig follows singleton pattern."""
        config1 = EnvConfig()
        config2 = EnvConfig()
        assert config1 is config2
    
    def test_bool_casting_variants(self):
        """Test various boolean string representations."""
        os.environ['BOOL_TRUE_1'] = 'true'
        os.environ['BOOL_TRUE_2'] = '1'
        os.environ['BOOL_TRUE_3'] = 'yes'
        os.environ['BOOL_TRUE_4'] = 'on'
        os.environ['BOOL_FALSE_1'] = 'false'
        os.environ['BOOL_FALSE_2'] = '0'
        os.environ['BOOL_FALSE_3'] = 'no'
        os.environ['BOOL_FALSE_4'] = 'off'
        
        assert env_config.get('BOOL_TRUE_1', bool) is True
        assert env_config.get('BOOL_TRUE_2', bool) is True
        assert env_config.get('BOOL_TRUE_3', bool) is True
        assert env_config.get('BOOL_TRUE_4', bool) is True
        
        assert env_config.get('BOOL_FALSE_1', bool) is False
        assert env_config.get('BOOL_FALSE_2', bool) is False
        assert env_config.get('BOOL_FALSE_3', bool) is False
        assert env_config.get('BOOL_FALSE_4', bool) is False
    
    def test_env_validation_error_message(self):
        """Test error message contains helpful information."""
        env_config.register_required('VAR_1')
        env_config.register_required('VAR_2')
        
        with pytest.raises(EnvValidationError) as exc_info:
            env_config.validate(fail_fast=True)
        
        error_msg = str(exc_info.value)
        assert 'VAR_1' in error_msg
        assert 'VAR_2' in error_msg
        assert 'Missing' in error_msg

class TestValidateEnvironment:
    """Tests for the validate_environment convenience function."""
    
    def setup_method(self):
        """Reset environment before each test."""
        self.original_env = os.environ.copy()
        env_config._initialized = False
        env_config.__init__()
    
    def teardown_method(self):
        """Restore environment after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_validate_environment_with_missing_vars(self):
        """Test validate_environment raises on missing vars."""
        with pytest.raises(EnvValidationError):
            validate_environment()
    
    def test_validate_environment_with_valid_vars(self):
        """Test validate_environment passes with valid vars."""
        os.environ['PROJECT_ROOT'] = str(Path.cwd())
        os.environ['DATA_DIR'] = str(Path.cwd() / 'data')
        os.environ['LOG_LEVEL'] = 'INFO'
        
        # Should not raise
        validate_environment()
    
    def test_validate_environment_loads_dotenv(self):
        """Test that validate_environment loads .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('PROJECT_ROOT=/test/root\n')
            f.write('DATA_DIR=/test/data\n')
            f.write('LOG_LEVEL=DEBUG\n')
            env_path = f.name
        
        try:
            # Temporarily change cwd to where .env is
            original_cwd = os.getcwd()
            os.chdir(Path(env_path).parent)
            
            validate_environment()
            
            assert os.environ.get('PROJECT_ROOT') == '/test/root'
            assert os.environ.get('DATA_DIR') == '/test/data'
            assert os.environ.get('LOG_LEVEL') == 'DEBUG'
        finally:
            os.chdir(original_cwd)
            os.unlink(env_path)

class TestEnvConfigPersistence:
    """Tests for configuration persistence across calls."""
    
    def setup_method(self):
        """Reset environment before each test."""
        self.original_env = os.environ.copy()
        env_config._initialized = False
        env_config.__init__()
    
    def teardown_method(self):
        """Restore environment after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_config_registers_persist(self):
        """Test that registered variables persist across validate calls."""
        env_config.register_required('PERSIST_VAR', default='default')
        
        # First validation
        env_config.validate(fail_fast=True)
        assert os.environ.get('PERSIST_VAR') == 'default'
        
        # Second validation (should still have the var)
        env_config.validate(fail_fast=True)
        assert os.environ.get('PERSIST_VAR') == 'default'
    
    def test_multiple_validations_dont_duplicate(self):
        """Test multiple validations don't cause issues."""
        env_config.register_required('MULTI_VAR', default='value')
        
        for _ in range(3):
            env_config.validate(fail_fast=True)
        
        # Should still be single instance
        assert env_config.get('MULTI_VAR') == 'value'