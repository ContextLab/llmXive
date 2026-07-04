"""
Tests for the Instrument Validator (T024a).
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
code_path = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_path))

from validation.instrument_validator import (
    validate_citation,
    run_validation_agent,
    generate_report_md,
    PRIMARY_SOURCES
)

def test_validate_citation_known():
    """Test validation of a known valid instrument."""
    is_valid, message = validate_citation("cognitive_fluid_intelligence", PRIMARY_SOURCES["cognitive_fluid_intelligence"])
    assert is_valid is True
    assert "verified" in message.lower()

def test_validate_citation_unknown():
    """Test validation of an unknown instrument."""
    is_valid, message = validate_citation("unknown_instrument_xyz", {})
    assert is_valid is False
    assert "not found" in message.lower()

def test_validate_citation_field_id():
    """Test validation using a field ID string."""
    # Assuming 20016 is a valid field ID in our mock data
    is_valid, message = validate_citation("20016", {})
    assert is_valid is True
    assert "verified" in message.lower()

def test_run_validation_agent():
    """Test the full agent execution."""
    data = run_validation_agent()
    assert "overall_status" in data
    assert "results" in data
    assert data["instruments_validated"] > 0
    assert all(isinstance(r["is_valid"], bool) for r in data["results"])

def test_generate_report_md():
    """Test report generation."""
    mock_data = {
        "agent_name": "TestAgent",
        "version": "1.0",
        "execution_time": "2023-01-01T00:00:00",
        "overall_status": "passed",
        "instruments_validated": 1,
        "results": [
            {"instrument_id": "test_id", "is_valid": True, "message": "Verified", "timestamp": "now"}
        ]
    }
    report = generate_report_md(mock_data)
    assert "Instrument Citation Validation Report" in report
    assert "test_id" in report
    assert "Verified Accuracy" in report

def test_report_file_creation():
    """Test that the main function creates the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_report.md"
        
        # Mock sys.argv to simulate command line args
        original_argv = sys.argv
        sys.argv = ["test_instrument_validator.py", "--output", str(output_file)]
        
        try:
            from validation.instrument_validator import main
            main()
            
            assert output_file.exists(), "Report file was not created."
            content = output_file.read_text()
            assert "Instrument Citation Validation Report" in content
        finally:
            sys.argv = original_argv
