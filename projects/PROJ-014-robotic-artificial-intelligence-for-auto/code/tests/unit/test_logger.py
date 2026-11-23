import os
import json
import time
import tempfile
from pathlib import Path
import pytest
import sys
import threading

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.logger import ResourceLogger, get_logger, log_metrics, start_logging, stop_logging, get_resource_summary

class TestResourceLogger:
    def test_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ResourceLogger(output_dir=tmpdir, filename_prefix="test")
            assert logger.output_dir == Path(tmpdir)
            assert logger.filename_prefix == "test"
            assert logger.metrics_buffer == []
            assert logger.interval == 1.0

    def test_log_metrics_flushes_to_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ResourceLogger(output_dir=tmpdir, filename_prefix="test")
            metrics = {"cpu_percent": 50.0, "ram_percent": 60.0, "ram_used_mb": 1024.0}
            
            logger.log_metrics(metrics)
            
            # Check that a file was created
            files = list(Path(tmpdir).glob("test_*.json"))
            assert len(files) == 1
            
            # Check content
            with open(files[0], 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["cpu_percent"] == 50.0
            assert "timestamp" in data[0]

    def test_start_and_stop_sampling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ResourceLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start_sampling(interval=0.1)
            
            # Wait for at least one sampling cycle
            time.sleep(0.2)
            
            logger.stop_sampling()
            
            # Verify files were created
            files = list(Path(tmpdir).glob("test_*.json"))
            assert len(files) >= 1

    def test_stop_logging_flushes_remaining_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ResourceLogger(output_dir=tmpdir, filename_prefix="test")
            logger.log_metrics({"test": 123})
            logger.stop_sampling()
            
            files = list(Path(tmpdir).glob("test_*.json"))
            assert len(files) >= 1
            
            with open(files[0], 'r') as f:
                data = json.load(f)
            assert any(item.get("test") == 123 for item in data)

class TestGlobalLoggerFunctions:
    def test_get_logger_returns_singleton(self):
        # Reset singleton for test
        import utils.logger as logger_module
        logger_module._logger_instance = None
        
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2

    def test_log_metrics_uses_global_logger(self):
        import utils.logger as logger_module
        logger_module._logger_instance = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override get_path to return our temp dir
            original_get_path = logger_module.get_path
            logger_module.get_path = lambda x: tmpdir
            
            try:
                log_metrics({"global_test": True})
                files = list(Path(tmpdir).glob("metrics_*.json"))
                assert len(files) >= 1
            finally:
                logger_module.get_path = original_get_path

    def test_start_logging_starts_thread(self):
        import utils.logger as logger_module
        logger_module._logger_instance = None
        logger_module._logging_thread = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger_module.get_path = lambda x: tmpdir
            
            start_logging(interval=0.1)
            
            # Thread should be alive
            assert logger_module._logging_thread is not None
            assert logger_module._logging_thread.is_alive()
            
            stop_logging()
            assert not logger_module._logging_thread.is_alive()

    def test_get_resource_summary_returns_valid_dict(self):
        summary = get_resource_summary()
        assert "cpu_percent" in summary
        assert "ram_percent" in summary
        assert "ram_used_mb" in summary
        assert isinstance(summary["cpu_percent"], float)
        assert isinstance(summary["ram_percent"], float)
        assert isinstance(summary["ram_used_mb"], float)