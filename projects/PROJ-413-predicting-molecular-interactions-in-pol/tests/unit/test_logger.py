"""
Unit tests for T008: code/utils/logger.py
"""
import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import PerformanceLogger, log_performance, get_memory_usage_mb, RESULTS_DIR, PERFORMANCE_FILE

class TestPerformanceLogger:
    """Tests for the PerformanceLogger class."""

    def test_context_manager_success(self, tmp_path):
        """Test that the context manager works on success."""
        # Temporarily override the file path for testing
        original_file = PERFORMANCE_FILE
        test_file = str(tmp_path / "test_perf.json")
        
        # Patch the module-level variable
        import utils.logger
        utils.logger.PERFORMANCE_FILE = test_file
        
        try:
            with PerformanceLogger("test_script") as logger:
                time.sleep(0.01)
            
            # Verify file exists
            assert os.path.exists(test_file)
            
            # Verify content
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["script_name"] == "test_script"
            assert data[0]["status"] == "success"
            assert data[0]["duration_seconds"] is not None
            assert data[0]["duration_seconds"] >= 0.01
        finally:
            # Restore original
            utils.logger.PERFORMANCE_FILE = original_file

    def test_context_manager_failure(self, tmp_path):
        """Test that the context manager handles exceptions."""
        original_file = PERFORMANCE_FILE
        test_file = str(tmp_path / "test_perf_fail.json")
        
        import utils.logger
        utils.logger.PERFORMANCE_FILE = test_file
        
        try:
            try:
                with PerformanceLogger("fail_script") as logger:
                    raise ValueError("Test error")
            except ValueError:
                pass  # Expected
            
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["status"] == "failed"
            assert data[0]["error"] is not None
            assert data[0]["error"]["type"] == "ValueError"
        finally:
            utils.logger.PERFORMANCE_FILE = original_file

    def test_manual_log_performance(self, tmp_path):
        """Test the convenience function log_performance."""
        original_file = PERFORMANCE_FILE
        test_file = str(tmp_path / "test_perf_manual.json")
        
        import utils.logger
        utils.logger.PERFORMANCE_FILE = test_file
        
        try:
            log_performance(
                script_name="manual_test",
                duration=0.5,
                memory_mb=256.0,
                status="success"
            )
            
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["script_name"] == "manual_test"
            assert data[0]["duration_seconds"] == 0.5
            assert data[0]["memory_usage_mb"] == 256.0
            assert data[0]["max_memory_mb"] == 256.0
        finally:
            utils.logger.PERFORMANCE_FILE = original_file

    def test_append_multiple_entries(self, tmp_path):
        """Test that multiple runs append to the file."""
        original_file = PERFORMANCE_FILE
        test_file = str(tmp_path / "test_perf_append.json")
        
        import utils.logger
        utils.logger.PERFORMANCE_FILE = test_file
        
        try:
            # First run
            with PerformanceLogger("run1") as l1:
                time.sleep(0.01)
            
            # Second run
            with PerformanceLogger("run2") as l2:
                time.sleep(0.01)
            
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]["script_name"] == "run1"
            assert data[1]["script_name"] == "run2"
        finally:
            utils.logger.PERFORMANCE_FILE = original_file

class TestGetMemoryUsage:
    """Tests for get_memory_usage_mb helper."""

    def test_returns_float_or_none(self):
        """Test that the function returns a number or None."""
        result = get_memory_usage_mb()
        assert result is None or isinstance(result, float)
        if result is not None:
            assert result > 0