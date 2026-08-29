import pytest
import yaml
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.logging_init import ConfigError, load_logging_config, setup_global_logger

@pytest.fixture
def valid_logging_config():
    return {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "handlers": ["console", "file"]
    }

@pytest.fixture
def invalid_logging_config_missing_level():
    return {
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "handlers": ["console", "file"]
    }

@pytest.fixture
def invalid_logging_config_missing_format():
    return {
        "level": "INFO",
        "handlers": ["console", "file"]
    }

@pytest.fixture
def invalid_logging_config_missing_handlers():
    return {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }

def test_load_logging_config_valid(tmp_path, valid_logging_config):
    config_file = tmp_path / "logging_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(valid_logging_config, f)
    
    config = load_logging_config(str(config_file))
    assert config["level"] == "INFO"
    assert "handlers" in config
    assert len(config["handlers"]) == 2

def test_load_logging_config_missing_level(tmp_path, invalid_logging_config_missing_level):
    config_file = tmp_path / "logging_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(invalid_logging_config_missing_level, f)
    
    with pytest.raises(ConfigError) as exc_info:
        load_logging_config(str(config_file))
    assert "level" in str(exc_info.value)

def test_load_logging_config_missing_format(tmp_path, invalid_logging_config_missing_format):
    config_file = tmp_path / "logging_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(invalid_logging_config_missing_format, f)
    
    with pytest.raises(ConfigError) as exc_info:
        load_logging_config(str(config_file))
    assert "format" in str(exc_info.value)

def test_load_logging_config_missing_handlers(tmp_path, invalid_logging_config_missing_handlers):
    config_file = tmp_path / "logging_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(invalid_logging_config_missing_handlers, f)
    
    with pytest.raises(ConfigError) as exc_info:
        load_logging_config(str(config_file))
    assert "handlers" in str(exc_info.value)

def test_setup_global_logger_valid(tmp_path, valid_logging_config):
    config_file = tmp_path / "logging_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(valid_logging_config, f)
    
    # Mock get_project_root to return tmp_path
    with patch('code.utils.logging_init.get_project_root', return_value=tmp_path.parent):
        logger = setup_global_logger(str(config_file))
        assert logger is not None
        assert logger.level == 20  # INFO level
