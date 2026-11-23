"""
Unit tests for T053: Robustness Summary Report Generation
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module functions
from code.generate_robustness_summary import (
    load_json_file,
    extract_key_result,
    format_result_table,
    generate_sensitivity_section,
    generate_robustness_summary,
    main
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_json_file_success(temp_dir):
    """Test loading a valid JSON file."""
    test_file = temp_dir / "test.json"
    test_data = {"key": "value", "number": 42}
    with open(test_file, 'w') as f:
        json.dump(test_data, f)
    
    result = load_json_file(test_file)
    assert result == test_data

def test_load_json_file_not_found(temp_dir):
    """Test loading a non-existent file raises FileNotFoundError."""
    missing_file = temp_dir / "missing.json"
    with pytest.raises(FileNotFoundError):
        load_json_file(missing_file)

def test_extract_key_result_found():
    """Test extracting a key that exists."""
    report = {
        "p_values": {
            "perseverative_errors_nostalgia_vs_control": 0.03
        }
    }
    result = extract_key_result(report, "perseverative_errors", "nostalgia_vs_control")
    assert result == "0.03"

def test_extract_key_result_not_found():
    """Test extracting a key that does not exist returns None."""
    report = {
        "p_values": {
            "other_metric": 0.05
        }
    }
    result = extract_key_result(report, "missing_metric", "test")
    assert result is None

def test_format_result_table():
    """Test formatting the comparison table."""
    primary = {
        "p_values": {
            "perseverative_errors_nostalgia_vs_control": 0.03,
            "categories_completed_nostalgia_vs_control": 0.04
        }
    }
    robustness = {
        "p_values": {
            "perseverative_errors_nostalgia_vs_control": 0.031,
            "categories_completed_nostalgia_vs_control": 0.042
        }
    }
    
    table = format_result_table(primary, robustness)
    assert "perseverative_errors" in table
    assert "categories_completed" in table
    assert "Primary (MMSE >= 24)" in table

def test_generate_sensitivity_section():
    """Test generating the sensitivity analysis section."""
    sensitivity_report = {
        "thresholds": [
            {
                "alpha": 0.05,
                "p_value_perseverative_errors": 0.03,
                "p_value_categories_completed": 0.06,
                "is_sensitive_to_threshold": False
            }
        ]
    }
    
    section = generate_sensitivity_section(sensitivity_report)
    assert "0.05" in section
    assert "Perseverative Errors" in section
    assert "Categories Completed" in section

def test_generate_robustness_summary_stable():
    """Test generating the full report with stable results."""
    primary = {"p_values": {"test": 0.03}}
    robustness = {"status": "OK", "p_values": {"test": 0.031}}
    sensitivity = {"thresholds": []}
    comparison = {"is_stable": True}
    
    report = generate_robustness_summary(primary, robustness, sensitivity, comparison)
    
    assert "# Robustness Summary Report" in report
    assert "Final Verdict" in report
    assert "holds across all conditions" in report

def test_generate_robustness_summary_skipped():
    """Test generating the report when robustness check is skipped."""
    primary = {"p_values": {"test": 0.03}}
    robustness = {"status": "SKIPPED", "reason": "MMSE_MISSING"}
    sensitivity = {"thresholds": []}
    comparison = {}
    
    report = generate_robustness_summary(primary, robustness, sensitivity, comparison)
    
    assert "skipped due to missing MMSE data" in report

@patch('code.generate_robustness_summary.load_json_file')
@patch('code.generate_robustness_summary.Path')
def test_main_execution(mock_path, mock_load, temp_dir):
    """Test the main function execution flow."""
    # Setup mocks
    mock_path_obj = MagicMock()
    mock_path_obj.exists.return_value = True
    mock_path_obj.parent.mkdir.return_value = None
    mock_path.return_value = mock_path_obj
    
    mock_load.return_value = {
        "p_values": {"test": 0.03},
        "status": "OK",
        "thresholds": [],
        "is_stable": True
    }
    
    # Mock open to capture written content
    with patch('builtins.open', MagicMock()) as mock_open:
        main()
        
        # Verify open was called
        assert mock_open.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])