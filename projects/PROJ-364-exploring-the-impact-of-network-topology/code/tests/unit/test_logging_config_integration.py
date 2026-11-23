import logging
import tempfile
from pathlib import Path
import pytest
import configparser

def test_logging_config_loads_and_writes_file():
    """Integration test: verify logging.conf loads and writes to the correct file."""
    config_path = Path("code/logging.conf")
    assert config_path.exists(), "logging.conf must exist"
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "logs"
        log_dir.mkdir()
        log_file = log_dir / "pipeline.log"
        
        # Read and modify the config to use our temp log file
        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Update the file handler args to point to our temp file
        # This is a bit hacky but necessary for testing
        original_args = config['handler_fileHandler']['args']
        # Replace 'logs/pipeline.log' with the temp file path
        modified_args = f"('{log_file}', 'a')"
        config['handler_fileHandler']['args'] = modified_args
        
        # Apply the configuration
        logging.config.fileConfig(config, disable_existing_loggers=False)
        
        # Get a logger and log a message
        logger = logging.getLogger('data_ingestion')
        test_message = "Test message for integration"
        logger.info(test_message)
        
        # Verify the log file was created and contains the message
        assert log_file.exists(), "Log file should be created"
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert test_message in content, f"Log message '{test_message}' should be in log file"
            
            # Verify the format includes timestamp, name, level, and message
            lines = content.strip().split('\n')
            assert len(lines) > 0
            log_line = lines[0]
            assert 'data_ingestion' in log_line, "Log line should contain logger name"
            assert 'INFO' in log_line, "Log line should contain log level"
            assert test_message in log_line, "Log line should contain the message"