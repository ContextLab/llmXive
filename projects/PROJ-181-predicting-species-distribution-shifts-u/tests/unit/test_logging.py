import pytest
import os
import logging
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.logging_config import (
    setup_logger,
    get_logger,
    get_preprocess_logger,
    get_download_logger,
    get_train_logger,
    get_project_logger,
    DetailedFormatter,
    initialize_pipeline_logging
)
from code.utils.yaml_utils import write_preprocess_counts, read_yaml_file
from code.config import LOGS_DIR

class TestLoggerSetup:
    """Test logger initialization and configuration."""

    def test_setup_logger_creates_logger(self):
        """Test that setup_logger creates a logger with correct name."""
        logger_name = "test_logger"
        logger = setup_logger(logger_name)
        
        assert logger.name == logger_name
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logger_with_file(self, tmp_path):
        """Test that setup_logger creates a file handler when log_file is provided."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file_logger", log_file=str(log_file))
        
        assert len(logger.handlers) >= 2  # File + Console
        
        # Check file was created
        assert log_file.exists()

    def test_detailed_formatter_format(self):
        """Test that DetailedFormatter produces expected format."""
        formatter = DetailedFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Check format includes required components
        assert "test" in formatted  # name
        assert "INFO" in formatted  # level
        assert "Test message" in formatted  # message
        assert any(char.isdigit() for char in formatted)  # timestamp

    def test_get_logger_reuses_existing(self):
        """Test that get_logger reuses an existing logger."""
        logger_name = "test_reuse_logger"
        logger1 = setup_logger(logger_name)
        logger2 = get_logger(logger_name)
        
        assert logger1 is logger2

    def test_initialize_pipeline_logging(self):
        """Test pipeline logging initialization."""
        root_logger = initialize_pipeline_logging()
        
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) >= 2  # Console + File

class TestPreprocessLogger:
    """Test preprocess-specific logger and YAML output."""

    def test_get_preprocess_logger(self):
        """Test that get_preprocess_logger returns a configured logger."""
        logger = get_preprocess_logger()
        
        assert logger.name == "preprocess"
        assert len(logger.handlers) > 0

    def test_write_preprocess_counts(self, tmp_path):
        """Test writing preprocess counts to YAML."""
        output_path = tmp_path / "test_counts.yaml"
        
        result_path = write_preprocess_counts(
            species="TestSpecies",
            before_count=1000,
            after_count=850,
            distance_used_km=10.0,
            output_path=str(output_path)
        )
        
        assert Path(result_path).exists()
        
        # Verify YAML content
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["species"] == "TestSpecies"
        assert data["before_count"] == 1000
        assert data["after_count"] == 850
        assert data["distance_used_km"] == 10.0
        assert "timestamp" in data

    def test_write_preprocess_counts_default_path(self):
        """Test writing to default log path."""
        result_path = write_preprocess_counts(
            species="DefaultPathSpecies",
            before_count=500,
            after_count=400,
            distance_used_km=10.0
        )
        
        expected_path = LOGS_DIR / "preprocess_counts.yaml"
        assert result_path == str(expected_path)
        assert expected_path.exists()

    def test_read_yaml_file(self, tmp_path):
        """Test reading a YAML file."""
        test_data = {
            "species": "ReadTest",
            "before_count": 200,
            "after_count": 150,
            "timestamp": "2024-01-01T00:00:00",
            "distance_used_km": 10.0
        }
        
        test_file = tmp_path / "test_read.yaml"
        with open(test_file, 'w') as f:
            yaml.dump(test_data, f)
        
        result = read_yaml_file(str(test_file))
        
        assert result["species"] == "ReadTest"
        assert result["before_count"] == 200
        assert result["distance_used_km"] == 10.0

    def test_read_yaml_file_not_found(self):
        """Test reading a non-existent YAML file raises error."""
        with pytest.raises(FileNotFoundError):
            read_yaml_file("/nonexistent/path/file.yaml")

    def test_yaml_schema_compliance(self, tmp_path):
        """Test that written YAML matches required schema."""
        output_path = tmp_path / "schema_test.yaml"
        
        write_preprocess_counts(
            species="SchemaTest",
            before_count=100,
            after_count=90,
            distance_used_km=10.0,
            output_path=str(output_path)
        )
        
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Verify all required fields exist with correct types
        assert isinstance(data["species"], str)
        assert isinstance(data["before_count"], int)
        assert isinstance(data["after_count"], int)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["distance_used_km"], float)

class TestOtherLoggers:
    """Test other specialized loggers."""

    def test_get_download_logger(self):
        """Test download logger creation."""
        logger = get_download_logger()
        assert logger.name == "download"

    def test_get_train_logger(self):
        """Test training logger creation."""
        logger = get_train_logger()
        assert logger.name == "train"

    def test_get_project_logger(self):
        """Test project logger creation."""
        logger = get_project_logger()
        assert logger.name == "project"
