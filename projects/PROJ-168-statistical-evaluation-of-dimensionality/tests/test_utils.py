"""
Tests for code/utils.py resource monitoring and logging utilities.
"""
import os
import sys
import time
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code to path if not already
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils import (
    get_current_ram_mb,
    check_ram_limit,
    log_metric,
    resource_abort_wrapper,
    run_with_time_logging,
    ensure_monitoring_dir,
    RAM_LIMIT_GB
)
from config import Config

class TestResourceMonitoring:
    """Tests for RAM monitoring functions."""

    def test_get_current_ram_mb_returns_positive(self):
        """Test that get_current_ram_mb returns a positive number."""
        ram = get_current_ram_mb()
        assert isinstance(ram, float)
        assert ram >= 0

    def test_check_ram_limit_with_high_limit(self):
        """Test check_ram_limit returns False when limit is high."""
        # Set a very high limit (1000 GB)
        assert check_ram_limit(limit_gb=1000.0) is False

    def test_check_ram_limit_with_zero_limit(self):
        """Test check_ram_limit returns True when limit is zero."""
        # Set a zero limit, should always trigger
        assert check_ram_limit(limit_gb=0.0) is True

    def test_log_metric_creates_file(self, tmp_path):
        """Test that log_metric creates the monitoring CSV file."""
        # Mock Config to use temp directory
        original_results = Config.RESULTS_DIR
        Config.RESULTS_DIR = str(tmp_path / "results")
        
        try:
            log_metric("test_step", "test_metric", 1.0, "units", "ok")
            
            file_path = Path(Config.RESULTS_DIR) / "monitoring.csv"
            assert file_path.exists()
            
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 2 # Header + 1 data row
                assert rows[0] == ['timestamp', 'step_name', 'metric_name', 'value', 'unit', 'status']
                assert rows[1][1] == 'test_step'
                assert rows[1][2] == 'test_metric'
        finally:
            Config.RESULTS_DIR = original_results

    def test_log_metric_appends_data(self, tmp_path):
        """Test that log_metric appends to existing file."""
        original_results = Config.RESULTS_DIR
        Config.RESULTS_DIR = str(tmp_path / "results")
        
        try:
            log_metric("step1", "m1", 1.0, "u", "ok")
            log_metric("step2", "m2", 2.0, "u", "ok")
            
            file_path = Path(Config.RESULTS_DIR) / "monitoring.csv"
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 3 # Header + 2 data rows
        finally:
            Config.RESULTS_DIR = original_results

class TestResourceAbortWrapper:
    """Tests for the resource_abort_wrapper decorator."""

    def test_wrapper_logs_on_success(self, tmp_path):
        """Test that wrapper logs metrics on successful execution."""
        original_results = Config.RESULTS_DIR
        Config.RESULTS_DIR = str(tmp_path / "results")
        
        try:
            @resource_abort_wrapper(limit_gb=1000.0)
            def dummy_func():
                return "success"
            
            result = dummy_func()
            assert result == "success"
            
            file_path = Path(Config.RESULTS_DIR) / "monitoring.csv"
            assert file_path.exists()
            
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                # Header + duration + peak_ram
                assert len(rows) >= 3
                # Check for duration metric
                metrics = [r[2] for r in rows[1:]]
                assert 'duration_sec' in metrics
        finally:
            Config.RESULTS_DIR = original_results

    def test_wrapper_raises_on_ram_exceed(self, tmp_path):
        """Test that wrapper raises MemoryError if RAM limit is exceeded."""
        original_results = Config.RESULTS_DIR
        Config.RESULTS_DIR = str(tmp_path / "results")
        
        try:
            @resource_abort_wrapper(limit_gb=0.0) # 0 GB limit
            def dummy_func():
                return "success"
            
            with pytest.raises(MemoryError):
                dummy_func()
        finally:
            Config.RESULTS_DIR = original_results

class TestRunWithTimeLogging:
    """Tests for run_with_time_logging function."""

    def test_run_with_time_logging_executes_and_logs(self, tmp_path):
        """Test that run_with_time_logging executes function and logs metrics."""
        original_results = Config.RESULTS_DIR
        Config.RESULTS_DIR = str(tmp_path / "results")
        
        try:
            def dummy_func():
                time.sleep(0.1)
                return "done"
            
            result = run_with_time_logging("test_step", dummy_func)
            assert result == "done"
            
            file_path = Path(Config.RESULTS_DIR) / "monitoring.csv"
            assert file_path.exists()
            
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                # Should have duration and peak_ram logs
                metrics = [r[2] for r in rows[1:]]
                assert 'duration_sec' in metrics
        finally:
            Config.RESULTS_DIR = original_results

class TestEnsureMonitorDir:
    """Tests for ensure_monitoring_dir."""

    def test_ensure_monitoring_dir_creates_directory(self, tmp_path):
        """Test that ensure_monitoring_dir creates the results directory."""
        original_results = Config.RESULTS_DIR
        Config.RESULTS_DIR = str(tmp_path / "results")
        
        try:
            assert not Path(Config.RESULTS_DIR).exists()
            ensure_monitoring_dir()
            assert Path(Config.RESULTS_DIR).exists()
        finally:
            Config.RESULTS_DIR = original_results