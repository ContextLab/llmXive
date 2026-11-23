"""
Unit tests for code/utils.py
Verifies error handling classes and logging utilities.
"""
import pytest
import sys
import logging
from pathlib import Path

# Ensure imports work from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import DataAvailabilityError, VoronoiFailure, get_logger, log_audit_event

def test_data_availability_error():
    """Test that DataAvailabilityError raises with correct message."""
    with pytest.raises(DataAvailabilityError) as exc_info:
        raise DataAvailabilityError("Data missing: thermal_conductivity")
    
    assert "Data missing: thermal_conductivity" in str(exc_info.value)
    assert exc_info.value.exit_code == 1

def test_voronoi_failure():
    """Test that VoronoiFailure raises with correct message."""
    with pytest.raises(VoronoiFailure) as exc_info:
        raise VoronoiFailure("Voronoi tessellation failed for snapshot 1")
    
    assert "Voronoi tessellation failed for snapshot 1" in str(exc_info.value)
    assert exc_info.value.exit_code == 2

def test_get_logger():
    """Test that get_logger returns a configured logger."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"

def test_log_audit_event():
    """Test that log_audit_event writes to the audit log."""
    # This is a basic smoke test. In a real scenario, we might mock the file write.
    # We verify the function call doesn't crash and produces a log entry.
    logger = get_logger("test_audit")
    
    # Capture log output
    import io
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    
    log_audit_event(logger, "test_event", {"key": "value"})
    
    output = stream.getvalue()
    assert "test_event" in output
    assert "key" in output
    assert "value" in output
    
    logger.removeHandler(handler)
