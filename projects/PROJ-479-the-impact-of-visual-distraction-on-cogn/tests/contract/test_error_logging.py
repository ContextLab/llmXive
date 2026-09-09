import os
import pytest
import logging
import json
import sys
from io import StringIO
from unittest.mock import patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils import log_structured_error, get_logger

@pytest.fixture
def log_capture():
    """Capture log output."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.ERROR)
    logger = get_logger("test_error_logging")
    logger.addHandler(handler)
    yield log_stream
    logger.removeHandler(handler)

def test_unmatched_participant_ids(log_capture):
    """Test logging of unmatched_participant_ids error."""
    log_structured_error(
        "unmatched_participant_ids",
        "Failed to match participant IDs between datasets.",
        {"unmatched": ["P001", "P002"]}
    )
    
    log_output = log_capture.getvalue()
    assert "unmatched_participant_ids" in log_output
    assert "Failed to match participant IDs" in log_output

def test_image_processing_failures(log_capture):
    """Test logging of image_processing_failures error."""
    log_structured_error(
        "image_processing_failures",
        "Failed to process image file.",
        {"image_path": "data/raw/test.jpg", "error": "Corrupted file"}
    )
    
    log_output = log_capture.getvalue()
    assert "image_processing_failures" in log_output
    assert "Failed to process image file" in log_output

def test_zero_variance_warning(log_capture):
    """Test logging of zero_variance_warning error."""
    log_structured_error(
        "zero_variance_warning",
        "Detected zero variance in a predictor variable.",
        {"variable": "visual_complexity"}
    )
    
    log_output = log_capture.getvalue()
    assert "zero_variance_warning" in log_output
    assert "Detected zero variance" in log_output

if __name__ == "__main__":
    pytest.main([__file__, "-v"])