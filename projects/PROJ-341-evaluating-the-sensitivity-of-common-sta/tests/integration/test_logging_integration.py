"""
Integration tests for logging functionality across the simulation pipeline.
"""
import os
import sys
import json
import tempfile
import logging
from io import StringIO
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.simulation.logging_config import (
    setup_logging, get_logger, log_simulation_params, log_seed_usage,
    log_iteration_status, log_test_result, log_warning_assumption_violated,
    log_fallback_triggered, log_output_file_written, log_error_details,
    log_shutdown, get_log_file_path
)
from code.simulation import get_rng

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file for testing."""
    log_path = tmp_path / "test_simulation.log"
    return str(log_path)

@pytest.fixture
def logger_with_temp_file(temp_log_file):
    """Setup logger with temporary log file."""
    logger = setup_logging(log_level="DEBUG", log_file=temp_log_file)
    return logger, temp_log_file

def test_setup_logging_creates_file(logger_with_temp_file):
    """Test that setup_logging creates the log file."""
    logger, log_file = logger_with_temp_file
    assert os.path.exists(log_file)
    assert os.path.getsize(log_file) > 0

def test_get_logger_returns_child(logger_with_temp_file):
    """Test that get_logger returns a child logger."""
    logger, _ = logger_with_temp_file
    child = get_logger("test.module")
    assert child.name.startswith("llmXive_simulation")

def test_log_simulation_params(logger_with_temp_file):
    """Test logging simulation parameters."""
    logger, log_file = logger_with_temp_file
    params = {
        "sample_size": 100,
        "effect_size": 0.5,
        "alpha": 0.05,
        "iterations": 1000
    }
    log_simulation_params(params, logger)
    
    # Verify log file contains the params
    with open(log_file, 'r') as f:
        content = f.read()
        assert "sample_size" in content
        assert "effect_size" in content
        assert "0.5" in content

def test_log_seed_usage(logger_with_temp_file):
    """Test logging seed usage."""
    logger, log_file = logger_with_temp_file
    log_seed_usage(42, "data_generator", logger)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Seed 42" in content
        assert "data_generator" in content

def test_log_iteration_status(logger_with_temp_file):
    """Test logging iteration status."""
    logger, log_file = logger_with_temp_file
    condition = {"n": 50, "effect": 0.3}
    log_iteration_status(50, 100, condition, 1.25, logger)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Iteration 50/100" in content
        assert "50.0%" in content
        assert "Elapsed: 1.25s" in content

def test_log_test_result(logger_with_temp_file):
    """Test logging test results."""
    logger, log_file = logger_with_temp_file
    log_test_result(
        test_type="t-test",
        p_value=0.032,
        statistic=2.15,
        sample_size=30,
        effect_size=0.5,
        hypothesis="alternative",
        logger=logger
    )
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "T-TEST" in content
        assert "p=0.032000" in content
        assert "n=30" in content

def test_log_warning_assumption_violated(logger_with_temp_file):
    """Test logging assumption violation warnings."""
    logger, log_file = logger_with_temp_file
    condition = {"n": 10, "test": "t-test"}
    log_warning_assumption_violated("Normality assumption violated", condition, logger)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "WARNING" in content
        assert "Normality assumption violated" in content

def test_log_fallback_triggered(logger_with_temp_file):
    """Test logging fallback test triggers."""
    logger, log_file = logger_with_temp_file
    log_fallback_triggered(
        original_test="chi-squared",
        fallback_test="fisher-exact",
        reason="Expected cell count < 5",
        logger=logger
    )
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "chi-squared" in content
        assert "fisher-exact" in content
        assert "Expected cell count < 5" in content

def test_log_output_file_written(logger_with_temp_file):
    """Test logging output file writes."""
    logger, log_file = logger_with_temp_file
    log_output_file_written("data/simulation/results.csv", 5000, logger)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "data/simulation/results.csv" in content
        assert "5000 records" in content

def test_log_error_details(logger_with_temp_file):
    """Test logging error details."""
    logger, log_file = logger_with_temp_file
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error_details(e, "test_function", logger)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "ERROR" in content
        assert "ValueError" in content
        assert "Test error" in content
        assert "Traceback" in content

def test_get_log_file_path(logger_with_temp_file):
    """Test getting the log file path."""
    logger, log_file = logger_with_temp_file
    path = get_log_file_path()
    assert path == log_file

def test_log_shutdown(logger_with_temp_file):
    """Test logging shutdown."""
    logger, log_file = logger_with_temp_file
    log_shutdown(logger)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Shutdown Complete" in content