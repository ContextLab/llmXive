import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.run_validation_skipped import write_skipped_validation_report, main
from code.utils.logging import get_logger

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_write_skipped_validation_report_creates_file(temp_output_dir):
    """
    Test that write_skipped_validation_report creates the file 
    with the correct JSON structure.
    """
    logger = get_logger("test_validation_skipped")
    output_file = temp_output_dir / "validation_report.txt"
    
    write_skipped_validation_report(logger, output_file)
    
    assert output_file.exists(), "Report file was not created."
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["status"] == "SKIPPED"
    assert data["reason"] == "No independent cohort available"
    assert data["sc_003_status"] == "Not Applicable"
    assert data["message"] == "Validation Skipped: No independent cohort available"
    assert data["details"]["cohort_found"] is False
    assert data["details"]["validation_performed"] is False

def test_write_skipped_validation_report_creates_parent_dir(temp_output_dir):
    """
    Test that the function creates parent directories if they don't exist.
    """
    logger = get_logger("test_validation_skipped")
    # Create a path with a non-existent parent subdirectory
    output_file = temp_output_dir / "subdir" / "validation_report.txt"
    
    write_skipped_validation_report(logger, output_file)
    
    assert output_file.exists(), "Report file was not created in nested directory."

def test_main_returns_zero_on_success(temp_output_dir, monkeypatch):
    """
    Test that main() returns 0 when successful.
    """
    # Mock get_output_path to return our temp file
    expected_path = temp_output_dir / "results" / "validation_report.txt"
    
    def mock_get_output_path(*args):
        return expected_path

    monkeypatch.setattr("code.run_validation_skipped.get_output_path", mock_get_output_path)
    
    # Ensure parent exists so the function doesn't fail on mkdir
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = main()
    
    assert result == 0, "main() should return 0 on success"
    assert expected_path.exists(), "Report file should be created by main()"

def test_main_returns_one_on_failure(temp_output_dir, monkeypatch):
    """
    Test that main() returns 1 when an exception occurs.
    """
    # Mock get_output_path to raise an exception
    def mock_get_output_path_fail(*args):
        raise RuntimeError("Simulated path error")
    
    monkeypatch.setattr("code.run_validation_skipped.get_output_path", mock_get_output_path_fail)
    
    result = main()
    
    assert result == 1, "main() should return 1 on failure"