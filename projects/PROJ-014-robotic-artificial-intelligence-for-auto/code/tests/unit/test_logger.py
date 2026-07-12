"""
Unit tests for the ResourceLogger module.
"""
import os
import json
import time
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.logger import ResourceLogger, log_metrics, get_logger, start_logging, stop_logging, get_resource_summary


class TestResourceLogger:
    """Tests for the ResourceLogger class."""

    def test_initialization_creates_file(self, tmp_path):
        """Test that initialization creates the log file with correct structure."""
        log_path = tmp_path / "test_log.json"
        logger = ResourceLogger(str(log_path), interval_seconds=0.1)
        
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            data = json.load(f)
            assert "logs" in data
            assert isinstance(data["logs"], list)

    def test_log_metrics_appends_entry(self, tmp_path):
        """Test that log_metrics appends a new entry to the log file."""
        log_path = tmp_path / "test_log.json"
        logger = ResourceLogger(str(log_path))
        
        test_metrics = {"accuracy": 0.95, "loss": 0.05}
        logger.log_metrics(test_metrics)
        
        with open(log_path, 'r') as f:
            data = json.load(f)
            assert len(data["logs"]) == 1
            assert "metrics" in data["logs"][0]
            assert data["logs"][0]["metrics"] == test_metrics
            assert "timestamp" in data["logs"][0]

    def test_sampling_creates_resource_entry(self, tmp_path):
        """Test that sampling creates a resource usage entry."""
        log_path = tmp_path / "test_log.json"
        logger = ResourceLogger(str(log_path), interval_seconds=0.1)
        
        # Sample once manually
        sample = logger._sample_resources()
        
        assert "timestamp" in sample
        assert "cpu_percent" in sample
        assert "ram_mb" in sample
        assert "ram_percent" in sample
        assert isinstance(sample["cpu_percent"], float)
        assert isinstance(sample["ram_mb"], float)

    def test_get_summary_returns_stats(self, tmp_path):
        """Test that get_summary returns correct statistics."""
        log_path = tmp_path / "test_log.json"
        logger = ResourceLogger(str(log_path))
        
        # Manually add some test entries
        logger._append_log({"cpu_percent": 10.0, "ram_mb": 100.0})
        logger._append_log({"cpu_percent": 20.0, "ram_mb": 200.0})
        logger._append_log({"cpu_percent": 30.0, "ram_mb": 300.0})
        
        summary = logger.get_summary()
        
        assert "total_samples" in summary
        assert summary["total_samples"] == 3
        assert summary["cpu"]["avg"] == 20.0
        assert summary["ram_mb"]["avg"] == 200.0
        assert summary["cpu"]["min"] == 10.0
        assert summary["cpu"]["max"] == 30.0

    def test_context_manager_starts_and_stops(self, tmp_path):
        """Test that context manager starts and stops sampling correctly."""
        log_path = tmp_path / "test_log.json"
        
        with patch.object(ResourceLogger, 'start_sampling') as mock_start:
            with patch.object(ResourceLogger, 'stop_sampling') as mock_stop:
                with ResourceLogger(str(log_path)) as logger:
                    mock_start.assert_called_once()
                    mock_stop.assert_not_called()
                
                mock_stop.assert_called_once()

    def test_start_and_stop_sampling(self, tmp_path):
        """Test explicit start and stop of sampling."""
        log_path = tmp_path / "test_log.json"
        logger = ResourceLogger(str(log_path))
        
        logger.start_sampling()
        assert logger._thread is not None
        assert logger._thread.is_alive()
        
        time.sleep(0.2)  # Let it run briefly
        
        logger.stop_sampling()
        assert not logger._thread.is_alive()


class TestGlobalLoggerFunctions:
    """Tests for global logger functions."""

    def setup_method(self):
        """Reset global logger before each test."""
        from src.utils import logger
        logger._global_logger = None

    def test_log_metrics_uses_global_logger(self, tmp_path):
        """Test that log_metrics uses the global logger."""
        log_path = tmp_path / "test_global_log.json"
        
        # Mock get_logger to return a logger with our temp path
        with patch('src.utils.logger.get_logger') as mock_get:
            mock_logger = MagicMock()
            mock_get.return_value = mock_logger
            
            log_metrics({"test": 123}, output_path=str(log_path))
            
            mock_get.assert_called_once_with(str(log_path))
            mock_logger.log_metrics.assert_called_once_with({"test": 123})

    def test_start_logging_returns_logger(self, tmp_path):
        """Test that start_logging returns a logger and starts it."""
        log_path = tmp_path / "test_start_log.json"
        
        with patch('src.utils.logger.get_logger') as mock_get:
            mock_logger = MagicMock()
            mock_get.return_value = mock_logger
            
            result = start_logging(output_path=str(log_path), interval_seconds=0.5)
            
            mock_get.assert_called_once_with(str(log_path), 0.5)
            mock_logger.start_sampling.assert_called_once()
            assert result == mock_logger

    def test_stop_logging_clears_global(self):
        """Test that stop_logging clears the global logger."""
        from src.utils import logger
        
        # Set a mock global logger
        logger._global_logger = MagicMock()
        
        stop_logging()
        
        assert logger._global_logger is None

    def test_get_resource_summary_returns_data(self, tmp_path):
        """Test that get_resource_summary returns summary data."""
        log_path = tmp_path / "test_summary_log.json"
        
        # Create a logger and add some data
        test_logger = ResourceLogger(str(log_path))
        test_logger._append_log({"cpu_percent": 50.0, "ram_mb": 500.0})
        
        # Mock get_logger to return our test logger
        with patch('src.utils.logger.get_logger') as mock_get:
            mock_get.return_value = test_logger
            
            summary = get_resource_summary(str(log_path))
            
            assert "total_samples" in summary
            assert summary["total_samples"] == 1

    def test_global_logger_singleton(self, tmp_path):
        """Test that get_logger returns the same instance."""
        log_path = tmp_path / "test_singleton_log.json"
        
        with patch('src.utils.logger._global_logger', None):
            with patch('src.utils.logger.ResourceLogger') as MockLogger:
                mock_instance = MagicMock()
                MockLogger.return_value = mock_instance
                
                logger1 = get_logger(str(log_path))
                logger2 = get_logger(str(log_path))
                
                # Should only create one instance
                MockLogger.assert_called_once()
                assert logger1 is logger2
