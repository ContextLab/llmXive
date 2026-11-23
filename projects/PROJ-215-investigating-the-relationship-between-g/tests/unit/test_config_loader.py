import os
import pytest
from unittest.mock import patch
from code.config_loader import (
    load_environment_variables, 
    get_config_value, 
    get_int_config, 
    get_float_config, 
    get_bool_config,
    initialize_config
)

def test_get_config_value_default():
    """Test that get_config_value returns default when key is missing."""
    # Ensure the key is not in the environment
    os.environ.pop('TEST_MISSING_KEY_12345', None)
    
    result = get_config_value('TEST_MISSING_KEY_12345', 'default_value')
    assert result == 'default_value'

def test_get_config_value_existing():
    """Test that get_config_value returns the env value when set."""
    os.environ['TEST_EXISTING_KEY_12345'] = 'env_value'
    
    result = get_config_value('TEST_EXISTING_KEY_12345', 'default_value')
    assert result == 'env_value'

    # Cleanup
    os.environ.pop('TEST_EXISTING_KEY_12345')

def test_get_int_config_valid():
    """Test parsing of valid integer string."""
    os.environ['TEST_INT_KEY'] = '123'
    assert get_int_config('TEST_INT_KEY') == 123
    os.environ.pop('TEST_INT_KEY')

def test_get_int_config_invalid():
    """Test that invalid integer string raises ValueError."""
    os.environ['TEST_INT_KEY'] = 'not_a_number'
    with pytest.raises(ValueError):
        get_int_config('TEST_INT_KEY')
    os.environ.pop('TEST_INT_KEY')

def test_get_float_config_valid():
    """Test parsing of valid float string."""
    os.environ['TEST_FLOAT_KEY'] = '3.14'
    assert get_float_config('TEST_FLOAT_KEY') == 3.14
    os.environ.pop('TEST_FLOAT_KEY')

def test_get_bool_config_true():
    """Test parsing of true boolean values."""
    for val in ['true', '1', 'yes', 'on', 'enabled']:
        os.environ['TEST_BOOL_KEY'] = val
        assert get_bool_config('TEST_BOOL_KEY') is True
        os.environ.pop('TEST_BOOL_KEY')

def test_get_bool_config_false():
    """Test parsing of false boolean values."""
    for val in ['false', '0', 'no', 'off', 'disabled']:
        os.environ['TEST_BOOL_KEY'] = val
        assert get_bool_config('TEST_BOOL_KEY') is False
        os.environ.pop('TEST_BOOL_KEY')

def test_get_bool_config_invalid():
    """Test that invalid boolean string raises ValueError."""
    os.environ['TEST_BOOL_KEY'] = 'maybe'
    with pytest.raises(ValueError):
        get_bool_config('TEST_BOOL_KEY')
    os.environ.pop('TEST_BOOL_KEY')

@patch('code.config_loader.load_dotenv')
@patch('code.config_loader.Path')
def test_load_environment_variables(mock_path, mock_load_dotenv, tmp_path):
    """Test that load_environment_variables calls dotenv correctly when file exists."""
    # Mock the path existence
    mock_path.return_value.exists.return_value = True
    
    load_environment_variables(str(tmp_path / ".env"))
    
    mock_load_dotenv.assert_called_once()

@patch('code.config_loader.load_dotenv')
@patch('code.config_loader.Path')
def test_load_environment_variables_missing_file(mock_path, mock_load_dotenv, tmp_path):
    """Test that load_environment_variables does nothing when file does not exist."""
    mock_path.return_value.exists.return_value = False
    
    load_environment_variables(str(tmp_path / ".env"))
    
    mock_load_dotenv.assert_not_called()
