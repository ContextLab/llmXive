"""
Unit tests for SMILES parsing and invalid entry logging.
Tests the logging infrastructure when invalid SMILES are encountered.
"""
import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path

# Import the logging utilities defined in the project
from src.utils.logging import get_logger, log_invalid_smiles

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files during testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_parse_smiles_invalid_logs_error(temp_log_dir):
    """
    Verify that log_invalid_smiles correctly logs invalid SMILES entries.
    
    This test:
    1. Sets up a logger that writes to a temporary file.
    2. Calls log_invalid_smiles with a known invalid SMILES string.
    3. Verifies that the log file contains the expected error message.
    """
    # Setup: Configure a logger that writes to a temporary file
    log_file_path = os.path.join(temp_log_dir, "test_parsing.log")
    
    # Get a logger instance (using a unique name to avoid conflicts with other tests)
    test_logger = get_logger("test_parsing_invalid_smiles", log_file=log_file_path)
    
    # Ensure the log file exists (logger might create it on first write)
    if not os.path.exists(log_file_path):
        # Force a log entry to ensure file creation
        test_logger.info("Initializing test log file")
    
    # Act: Log an invalid SMILES string
    invalid_smiles = "invalid_smiles_structure_123"
    source_file = "test_data.csv"
    line_number = 42
    
    log_invalid_smiles(
        logger=test_logger,
        smiles=invalid_smiles,
        source=source_file,
        line=line_number,
        reason="Invalid character in SMILES string"
    )
    
    # Assert: Check that the log file contains the error message
    assert os.path.exists(log_file_path), "Log file was not created"
    
    with open(log_file_path, 'r') as f:
        log_content = f.read()
    
    # Verify key components of the log message are present
    assert invalid_smiles in log_content, f"Invalid SMILES '{invalid_smiles}' not found in logs"
    assert source_file in log_content, f"Source file '{source_file}' not found in logs"
    assert str(line_number) in log_content, f"Line number '{line_number}' not found in logs"
    assert "ERROR" in log_content or "Invalid" in log_content, "Log message does not indicate an error/invalid entry"
    
    # Verify the log format matches expectations (contains the reason)
    assert "Invalid character" in log_content, "Log message does not contain the provided reason"

def test_log_invalid_smiles_handles_special_characters():
    """
    Verify that the logging function handles SMILES with special characters correctly.
    """
    # Setup: Create an in-memory handler to capture logs
    logger = logging.getLogger("test_special_chars")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid interference
    logger.handlers = []
    
    # Create a string handler to capture logs in memory
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    # Act: Log various invalid SMILES with special characters
    test_cases = [
        ("C[C@H](O)C(=O)N", "test.csv", 1, "Invalid stereochemistry notation"),
        ("C1CCCCC1[invalid]", "test.csv", 2, "Invalid bracket notation"),
        ("", "test.csv", 3, "Empty SMILES string"),
    ]
    
    for smiles, source, line, reason in test_cases:
        log_invalid_smiles(logger, smiles, source, line, reason)
    
    # Assert: Verify all entries were logged
    log_content = log_stream.getvalue()
    
    assert "Invalid stereochemistry notation" in log_content
    assert "Invalid bracket notation" in log_content
    assert "Empty SMILES string" in log_content
    assert "test.csv" in log_content

def test_log_invalid_smiles_with_none_values():
    """
    Verify that the logging function handles None values gracefully.
    """
    # Setup
    logger = logging.getLogger("test_none_values")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    # Act: Log with None values
    log_invalid_smiles(logger, None, None, None, "Test reason")
    
    # Assert: Should not raise an exception and should log something
    log_content = log_stream.getvalue()
    assert "Test reason" in log_content
    assert "None" in log_content or "unknown" in log_content.lower()