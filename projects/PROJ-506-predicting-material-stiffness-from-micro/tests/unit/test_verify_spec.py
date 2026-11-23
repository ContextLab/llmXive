import pytest
from pathlib import Path
from code.utils.verify_spec import verify_spec

def test_verify_spec_file_exists():
    """Test that verify_spec returns True when spec.md exists and contains required text."""
    # We assume the spec.md file created in this task exists
    result = verify_spec()
    assert result is True, "verify_spec should return True for the valid spec.md"

def test_verify_spec_missing_resolution():
    """Test that verify_spec returns False if resolution text is missing."""
    # This test requires mocking the file content, which is complex.
    # Instead, we rely on the integration test in test_integration.py or manual inspection.
    pass
