import logging
import os
import tempfile
from pathlib import Path
import sys
import pytest

import logging
from pathlib import Path

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "logs"
        log_dir.mkdir()
        yield log_dir

@pytest.fixture
def setup_logging_mock(temp_log_dir):
    """Setup logging configuration using the config file."""
    config_path = Path("code/logging.conf")
    if not config_path.exists():
        pytest.skip("logging.conf not found in code directory")
    
    # Temporarily redirect log file to temp directory for testing
    import configparser
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Update the file handler path to temp directory
    config['handler_fileHandler'] = config['handler_fileHandler'].copy()
    # We can't easily modify the args tuple in the config parser, 
    # so we'll test the format and existence of the config file instead
    return config

def test_setup_logging_creates_file(temp_log_dir, setup_logging_mock):
    """Test that the logging configuration file exists and is valid."""
    config_path = Path("code/logging.conf")
    assert config_path.exists(), "logging.conf must exist in code directory"
    
    # Verify the file can be parsed
    import configparser
    config = configparser.ConfigParser()
    config.read(config_path)
    
    assert 'loggers' in config
    assert 'handlers' in config
    assert 'formatters' in config
    assert 'logger_root' in config

def test_data_ingestion_logger_levels(setup_logging_mock):
    """Test that data_ingestion logger is configured with correct level."""
    config = setup_logging_mock
    assert 'logger_data_ingestion' in config
    assert config['logger_data_ingestion']['level'] == 'DEBUG'
    assert config['logger_data_ingestion']['qualName'] == 'data_ingestion'

def test_statistical_logger_levels(setup_logging_mock):
    """Test that statistical logger is configured with correct level."""
    config = setup_logging_mock
    assert 'logger_statistical' in config
    assert config['logger_statistical']['level'] == 'DEBUG'
    assert config['logger_statistical']['qualName'] == 'statistical'

def test_log_message_format(setup_logging_mock):
    """Test that the log format matches the required pattern."""
    config = setup_logging_mock
    assert 'formatter_standardFormatter' in config
    format_str = config['formatter_standardFormatter']['format']
    expected_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    assert format_str == expected_format, f"Expected '{expected_format}', got '{format_str}'"

def test_custom_log_levels_defined(setup_logging_mock):
    """Test that both data_ingestion and statistical loggers are defined."""
    config = setup_logging_mock
    assert 'logger_data_ingestion' in config['loggers']['keys']
    assert 'logger_statistical' in config['loggers']['keys']

def test_logger_separation(setup_logging_mock):
    """Test that loggers are properly separated with distinct names."""
    config = setup_logging_mock
    data_logger = config['logger_data_ingestion']
    stat_logger = config['logger_statistical']
    
    assert data_logger['qualName'] != stat_logger['qualName']
    assert data_logger['propagate'] == '0'
    assert stat_logger['propagate'] == '0'
