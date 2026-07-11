import os
import json
import time
import threading
import pytest
from unittest.mock import patch, MagicMock

# Ensure we can import from code/
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code import logging_config
from code import config

class TestLoggingConfig:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Setup: Initialize logging for each test
        logging_config.init_logging()
        yield
        # Teardown: Stop monitoring if running
        logging_config.stop_resource_monitoring()

    def test_init_logging_creates_files(self):
        """Test that init_logging creates the log files."""
        comp_path = logging_config.get_comparison_log_path()
        res_path = logging_config.get_resource_log_path()
        
        assert os.path.exists(comp_path), f"Comparison log {comp_path} not created"
        assert os.path.exists(res_path), f"Resource log {res_path} not created"

    def test_log_pairwise_comparison_writes_jsonl(self):
        """Test that log_pairwise_comparison writes a valid JSON line."""
        logging_config.log_pairwise_comparison(
            query_id="q1",
            doc_id_1="d1",
            doc_id_2="d2",
            similarity_score=0.95,
            is_wasted=True,
            model_name="test-model",
            latency_ms=10.5
        )

        path = logging_config.get_comparison_log_path()
        with open(path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        data = json.loads(lines[0])
        
        assert data["query_id"] == "q1"
        assert data["doc_id_1"] == "d1"
        assert data["doc_id_2"] == "d2"
        assert abs(data["similarity_score"] - 0.95) < 0.001
        assert data["is_wasted"] is True
        assert data["model_name"] == "test-model"
        assert abs(data["latency_ms"] - 10.5) < 0.001
        assert "timestamp" in data

    def test_log_pairwise_comparison_appends(self):
        """Test that multiple calls append to the log."""
        logging_config.log_pairwise_comparison("q1", "d1", "d2", 0.5, False, "m1", 1.0)
        logging_config.log_pairwise_comparison("q1", "d1", "d3", 0.8, True, "m1", 2.0)
        
        path = logging_config.get_comparison_log_path()
        with open(path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2

    def test_start_stop_resource_monitoring(self):
        """Test that resource monitoring can be started and stopped cleanly."""
        # Start
        logging_config.start_resource_monitoring()
        assert logging_config._resource_monitor_thread is not None
        assert logging_config._resource_monitor_thread.is_alive()
        
        # Wait a bit for at least one sample
        time.sleep(1.5)
        
        # Stop
        logging_config.stop_resource_monitoring()
        assert not logging_config._resource_monitor_thread.is_alive()
        
        # Check that resource log has entries
        path = logging_config.get_resource_log_path()
        with open(path, 'r') as f:
            lines = f.readlines()
        
        # Should have at least one entry (initial) + maybe more from the thread
        assert len(lines) >= 1

    def test_resource_monitoring_writes_valid_json(self):
        """Test that resource monitoring writes valid JSON entries."""
        logging_config.start_resource_monitoring()
        time.sleep(1.5)
        logging_config.stop_resource_monitoring()
        
        path = logging_config.get_resource_log_path()
        with open(path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) > 0
        for line in lines:
            data = json.loads(line)
            assert "timestamp" in data
            assert "cpu_time_user" in data
            assert "cpu_time_system" in data
            assert "max_memory_mb" in data

    def test_log_pairwise_comparison_raises_if_not_initialized(self):
        """Test that logging fails gracefully if not initialized."""
        # Reset state to simulate uninitialized state (careful with global state in tests)
        # We rely on the fact that if we don't call init_logging, paths are None
        # But since our fixture calls it, we manually override for this specific check
        original_path = logging_config._comparator_file_path
        logging_config._comparator_file_path = None
        
        try:
            with pytest.raises(RuntimeError):
                logging_config.log_pairwise_comparison("q1", "d1", "d2", 0.5, False, "m1", 1.0)
        finally:
            logging_config._comparator_file_path = original_path