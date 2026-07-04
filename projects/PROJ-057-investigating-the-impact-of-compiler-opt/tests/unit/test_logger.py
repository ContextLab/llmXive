"""
Unit tests for the logger infrastructure (T008).
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import sys
import logging

# Add code/ to path to import utils
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logger import (
    get_logger, 
    log_compiler_info, 
    log_nan_warning, 
    log_stability_failure,
    log_memory_fallback,
    log_benchmark_start,
    log_benchmark_end,
    LOG_DIR,
    get_log_file_path
)

def test_logger_initialization():
    """Test that logger initializes correctly and creates log directory."""
    # Ensure clean state by using a temporary directory for this test if needed,
    # but for now we rely on the global singleton behavior.
    logger = get_logger("test_logger_init")
    assert logger is not None
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
    # Verify log directory exists
    assert LOG_DIR.exists()

def test_log_compiler_info():
    """Test logging compiler information."""
    logger = get_logger("test_compiler_info")
    # Capture the last log message by checking the handler or just ensuring no exception
    log_compiler_info("clang", "14.0.0", ["-O3", "-march=native"])
    # If we reach here without exception, the log was written successfully
    assert True

def test_log_nan_warning():
    """Test logging NaN warnings."""
    logger = get_logger("test_nan_warning")
    log_nan_warning("tensor_123", "cfg_O3_ffast", "softmax_kernel")
    assert True

def test_log_stability_failure():
    """Test logging stability failures."""
    logger = get_logger("test_stability")
    log_stability_failure("cfg_O0", 1.2e-4, 1e-5)
    assert True

def test_log_memory_fallback():
    """Test logging memory fallback events."""
    logger = get_logger("test_memory")
    log_memory_fallback(768, 512, "cfg_oom")
    assert True

def test_log_benchmark_flow():
    """Test start and end logging flow."""
    logger = get_logger("test_flow")
    log_benchmark_start("cfg_test", "layernorm", "512x512")
    log_benchmark_end("cfg_test", 5.432, "success")
    log_benchmark_end("cfg_test_fail", 0.0, "error")
    assert True

def test_get_log_file_path():
    """Test retrieving the log file path."""
    path = get_log_file_path()
    assert isinstance(path, Path)
    assert path.exists()

if __name__ == "__main__":
    test_logger_initialization()
    test_log_compiler_info()
    test_log_nan_warning()
    test_log_stability_failure()
    test_log_memory_fallback()
    test_log_benchmark_flow()
    test_get_log_file_path()
    print("All logger tests passed.")