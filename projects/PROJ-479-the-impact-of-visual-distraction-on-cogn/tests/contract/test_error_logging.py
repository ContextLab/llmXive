"""
Contract test for error logging.
"""
import pytest
import logging
import json
from io import StringIO
from code.utils import log_structured_error, get_logger

def test_log_structured_error_keys():
    logger = get_logger("test_error")
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    
    log_structured_error("unmatched_participant_ids", {"count": 5}, logger)
    log_structured_error("image_processing_failures", {"file": "test.png"}, logger)
    
    output = stream.getvalue()
    lines = output.strip().split("\n")
    assert len(lines) == 2
    
    for line in lines:
        data = json.loads(line.split(" - ")[-1]) # Extract JSON part
        assert "error_type" in data
        assert data["error_type"] in ["unmatched_participant_ids", "image_processing_failures"]
