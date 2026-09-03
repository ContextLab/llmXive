import pytest
import tempfile
import os
from code.utils import setup_logging, pin_random_seed, compute_file_checksum

def test_setup_logging():
    """Test setup_logging with various signatures."""
    logger1 = setup_logging()
    assert logger1 is not None
    
    logger2 = setup_logging("INFO")
    assert logger2 is not None
    
    logger3 = setup_logging(log_level="DEBUG")
    assert logger3 is not None
    
    logger4 = setup_logging(name="test_logger")
    assert logger4 is not None
    
    logger5 = setup_logging("test_logger", "WARNING")
    assert logger5 is not None
    
    logger6 = setup_logging("test_logger", log_level="ERROR")
    assert logger6 is not None

def test_pin_random_seed():
    """Test pin_random_seed."""
    pin_random_seed(42)
    import numpy as np
    val1 = np.random.rand()
    
    pin_random_seed(42)
    val2 = np.random.rand()
    
    assert val1 == val2

def test_compute_file_checksum():
    """Test compute_file_checksum."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = compute_file_checksum(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
    finally:
        os.unlink(temp_path)
