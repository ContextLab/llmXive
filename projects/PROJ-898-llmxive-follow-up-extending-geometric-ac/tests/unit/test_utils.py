"""
Unit tests for code/utils.py.
"""
import os
import logging
import random
import numpy as np
import pytest
from code.utils import setup_logging, set_deterministic_seed, compute_sha256

def test_setup_logging_console(tmp_path):
    """Test that logging is configured correctly for console output."""
    logger = setup_logging(log_level=logging.DEBUG, logger_name="test_console_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0

def test_setup_logging_file(tmp_path):
    """Test that logging is configured correctly with a file handler."""
    log_file = tmp_path / "test.log"
    logger = setup_logging(
        log_level=logging.INFO, 
        log_file=str(log_file), 
        logger_name="test_file_logger"
    )
    assert isinstance(logger, logging.Logger)
    assert os.path.exists(log_file)
    
    logger.info("Test message")
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Test message" in content

def test_set_deterministic_seed():
    """Test that seeds are set correctly for reproducibility."""
    seed = 42
    
    # First run
    set_deterministic_seed(seed)
    val1_py = random.random()
    val1_np = np.random.rand()
    
    # Second run
    set_deterministic_seed(seed)
    val2_py = random.random()
    val2_np = np.random.rand()
    
    assert val1_py == val2_py, "Python random seed not deterministic"
    assert val1_np == val2_np, "Numpy random seed not deterministic"

def test_compute_sha256_string():
    """Test SHA-256 hashing of a string."""
    test_str = "llmXive-test-string"
    # Precomputed SHA-256 for "llmXive-test-string"
    expected_hash = "6981719248890368638575453374847253647586975864758647586475864758" # Dummy
    # Use actual hashlib for verification in test
    import hashlib
    expected = hashlib.sha256(test_str.encode('utf-8')).hexdigest()
    
    assert compute_sha256(test_str) == expected

def test_compute_sha256_bytes():
    """Test SHA-256 hashing of bytes."""
    test_bytes = b"llmXive-test-bytes"
    import hashlib
    expected = hashlib.sha256(test_bytes).hexdigest()
    
    assert compute_sha256(test_bytes) == expected

def test_compute_sha256_consistency():
    """Test that the same input always produces the same hash."""
    test_str = "consistency-check"
    hash1 = compute_sha256(test_str)
    hash2 = compute_sha256(test_str)
    assert hash1 == hash2