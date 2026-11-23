import pytest
import logging
import sys
from io import StringIO
from code.logging_config import (
    setup_logging, 
    get_module_logger, 
    log_skipped_row, 
    log_zero_variance_field,
    log_data_filter_step
)

def test_log_skipped_row_format(capsys):
    """Test that log_skipped_row produces the required warning format."""
    # Setup logger to capture output
    logger = setup_logging(level=logging.WARNING)
    
    # Mock a specific logger for testing to avoid cluttering root
    test_logger = get_module_logger("test_module_skipped")
    test_logger.setLevel(logging.WARNING)
    
    # Create a string handler to capture logs in memory
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    test_logger.addHandler(handler)
    
    # Call the function
    log_skipped_row(test_logger, 42, "NaN in effect_size")
    
    # Verify output
    log_output = stream.getvalue()
    assert "WARNING" in log_output
    assert "Skipping row 42" in log_output
    assert "NaN in effect_size" in log_output
    
    # Clean up
    test_logger.removeHandler(handler)

def test_log_zero_variance_field_format(capsys):
    """Test that log_zero_variance_field produces the required warning format."""
    test_logger = get_module_logger("test_module_var")
    test_logger.setLevel(logging.WARNING)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    test_logger.addHandler(handler)
    
    log_zero_variance_field(test_logger, "field_name", 1)
    
    log_output = stream.getvalue()
    assert "WARNING" in log_output
    assert "field_name" in log_output
    assert "1 unique" in log_output
    assert "zero variance" in log_output
    
    test_logger.removeHandler(handler)

def test_log_data_filter_step(capsys):
    """Test that log_data_filter_step logs the filtering operation details."""
    test_logger = get_module_logger("test_module_filter")
    test_logger.setLevel(logging.INFO)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    test_logger.addHandler(handler)
    
    log_data_filter_step(test_logger, "input.csv", "output.csv", 100, 90, "Dropped NaNs")
    
    log_output = stream.getvalue()
    assert "Data Filtering Step" in log_output
    assert "input.csv" in log_output
    assert "output.csv" in log_output
    assert "Rows before: 100" in log_output
    assert "Rows after: 90" in log_output
    
    test_logger.removeHandler(handler)