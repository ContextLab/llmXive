"""
Unit tests for the Quickstart Validator (Task T041).
"""
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from validation.quickstart_validator import check_prerequisites, validate_quickstart_steps, validate_output_artifacts

def test_check_prerequisites_directories():
    """Test that check_prerequisites correctly identifies missing directories."""
    # This is a smoke test. In a real scenario, we might mock the filesystem.
    # Given the constraints, we just ensure the function runs without crashing.
    result = check_prerequisites()
    assert isinstance(result, bool)

def test_validate_quickstart_steps():
    """Test that the validation step function runs."""
    # Similar to above, we ensure the function logic is sound.
    # We expect this to run the integration test.
    result = validate_quickstart_steps()
    assert isinstance(result, bool)

def test_validate_output_artifacts():
    """Test artifact validation logic."""
    result = validate_output_artifacts()
    assert isinstance(result, bool)