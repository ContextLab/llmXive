"""
Unit tests for the logging module.
"""
import pytest
from utils.logging import initialize_logging, log_provenance_mapping, flush_provenance_cache

def test_initialize_logging(tmp_path):
    """Test that logging is initialized correctly."""
    log_file = tmp_path / "test_provenance.log"
    
    # Initialize logging
    logger = initialize_logging(str(log_file))
    
    assert logger is not None
    assert log_file.exists()

def test_log_provenance_mapping(tmp_path):
    """Test logging a provenance mapping."""
    log_file = tmp_path / "test_provenance.log"
    initialize_logging(str(log_file))
    
    # Log a mapping
    log_provenance_mapping("conservation_tillage", "LSMS_12345", "Q5")
    
    # Flush to ensure data is written
    flush_provenance_cache()
    
    # Verify log file exists and has content
    assert log_file.exists()
    assert log_file.stat().st_size > 0