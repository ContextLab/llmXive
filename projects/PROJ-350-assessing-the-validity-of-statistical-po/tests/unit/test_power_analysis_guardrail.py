"""
Unit tests for T026a: Power Analysis Guardrail.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import csv

# Import the module to test
# Assuming the module is in code/ and we are running from project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from power_analysis_guardrail import load_power_analysis, filter_valid_records, main, MIN_STUDY_COUNT

@pytest.fixture
def temp_csv_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def create_csv_file(path: Path, rows: list):
    """Helper to create a CSV file with given rows."""
    if not rows:
        # Create empty file with headers if needed, or just empty
        path.touch()
        return

    fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def test_filter_valid_records_all_valid(temp_csv_dir):
    """Test filtering when all records are valid."""
    data = [
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": "1"},
        {"sensitivity_power": "0.95", "power_gap": "-0.05", "study_id": "2"},
    ]
    csv_path = temp_csv_dir / "test.csv"
    create_csv_file(csv_path, data)
    
    records = load_power_analysis(csv_path)
    valid = filter_valid_records(records)
    
    assert len(valid) == 2
    assert valid[0]["study_id"] == "1"

def test_filter_valid_records_invalid_power(temp_csv_dir):
    """Test filtering excludes invalid power values."""
    data = [
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": "1"}, # Valid
        {"sensitivity_power": "1.50", "power_gap": "0.10", "study_id": "2"}, # Invalid (>1)
        {"sensitivity_power": "", "power_gap": "0.10", "study_id": "3"},     # Empty
        {"sensitivity_power": "NaN", "power_gap": "0.10", "study_id": "4"},  # NaN string
    ]
    csv_path = temp_csv_dir / "test.csv"
    create_csv_file(csv_path, data)
    
    records = load_power_analysis(csv_path)
    valid = filter_valid_records(records)
    
    assert len(valid) == 1
    assert valid[0]["study_id"] == "1"

def test_filter_valid_records_invalid_gap(temp_csv_dir):
    """Test filtering excludes invalid power gap values."""
    data = [
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": "1"}, # Valid
        {"sensitivity_power": "0.80", "power_gap": "NaN", "study_id": "2"},  # NaN
        {"sensitivity_power": "0.80", "power_gap": "", "study_id": "3"},     # Empty
    ]
    csv_path = temp_csv_dir / "test.csv"
    create_csv_file(csv_path, data)
    
    records = load_power_analysis(csv_path)
    valid = filter_valid_records(records)
    
    assert len(valid) == 1

def test_filter_valid_records_error_flag(temp_csv_dir):
    """Test filtering excludes records with calculation_error flag."""
    data = [
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": "1", "calculation_error": "false"},
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": "2", "calculation_error": "true"},
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": "3", "calculation_error": "True"},
    ]
    csv_path = temp_csv_dir / "test.csv"
    create_csv_file(csv_path, data)
    
    records = load_power_analysis(csv_path)
    valid = filter_valid_records(records)
    
    assert len(valid) == 1
    assert valid[0]["study_id"] == "1"

def test_main_insufficient_count(temp_csv_dir, capsys):
    """Test that main returns 1 and writes error artifact when count < 30."""
    # Create a CSV with only 20 valid rows
    rows = [
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": str(i)}
        for i in range(20)
    ]
    csv_path = temp_csv_dir / "power_analysis.csv"
    create_csv_file(csv_path, rows)
    
    # Mock the global paths in the module to use our temp dir
    # This is a bit hacky but necessary for unit testing without mocking the whole module
    import power_analysis_guardrail as module
    
    original_input = module.INPUT_FILE
    original_error_dir = module.ERROR_OUTPUT_DIR
    original_error_file = module.ERROR_OUTPUT_FILE
    
    try:
        module.INPUT_FILE = csv_path
        module.ERROR_OUTPUT_DIR = temp_csv_dir / "results" / "error"
        module.ERROR_OUTPUT_FILE = module.ERROR_OUTPUT_DIR / "sample_size_insufficient.json"
        
        result = module.main()
        
        assert result == 1, "Expected exit code 1 for insufficient count"
        assert module.ERROR_OUTPUT_FILE.exists(), "Error artifact should be written"
        
        with open(module.ERROR_OUTPUT_FILE) as f:
            error_doc = json.load(f)
        
        assert error_doc["status"] == "HALTED"
        assert error_doc["details"]["actual_count"] == 20
        assert error_doc["details"]["required_minimum"] == 30
        
    finally:
        # Restore original paths
        module.INPUT_FILE = original_input
        module.ERROR_OUTPUT_DIR = original_error_dir
        module.ERROR_OUTPUT_FILE = original_error_file

def test_main_sufficient_count(temp_csv_dir, capsys):
    """Test that main returns 0 when count >= 30."""
    # Create a CSV with exactly 30 valid rows
    rows = [
        {"sensitivity_power": "0.80", "power_gap": "0.10", "study_id": str(i)}
        for i in range(30)
    ]
    csv_path = temp_csv_dir / "power_analysis.csv"
    create_csv_file(csv_path, rows)
    
    import power_analysis_guardrail as module
    
    original_input = module.INPUT_FILE
    
    try:
        module.INPUT_FILE = csv_path
        
        result = module.main()
        
        assert result == 0, "Expected exit code 0 for sufficient count"
        # Error file should NOT exist
        error_path = module.ERROR_OUTPUT_DIR / "sample_size_insufficient.json"
        # Note: We didn't change ERROR_OUTPUT_DIR in this test, so it points to real results/error
        # We just verify the return code is 0
        
    finally:
        module.INPUT_FILE = original_input
