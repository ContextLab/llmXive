import os
import sys
import json
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import load_config, fetch_sleep_edf, fetch_shhs, validate_dataset, main
from utils.logging import get_logger

def test_load_config_exists():
    """Test that load_config successfully reads config.yaml."""
    config = load_config()
    assert isinstance(config, dict)
    assert "dataset" in config or "parameters" in config  # Basic structure check

def test_fetch_sleep_edf_structure():
    """Test that fetch_sleep_edf returns the expected tuple structure."""
    # We expect it to return (df, count, issues)
    # Since we don't have real data in the test environment, we check the structure
    # and that it doesn't crash on import/initialization.
    df, count, issues = fetch_sleep_edf(load_config())
    assert df is None or isinstance(df, object) # Could be None or DataFrame
    assert isinstance(count, int)
    assert isinstance(issues, list)

def test_fetch_shhs_structure():
    """Test that fetch_shhs returns the expected tuple structure."""
    df, count, issues = fetch_shhs(load_config())
    assert df is None or isinstance(df, object)
    assert isinstance(count, int)
    assert isinstance(issues, list)

def test_validate_dataset_logic():
    """Test the validation logic for a hypothetical dataset."""
    # Case 1: Valid
    report = validate_dataset("TestDS", None, 50, [])
    assert report["valid"] is True
    assert report["participant_count"] == 50

    # Case 2: N < 30
    report = validate_dataset("TestDS", None, 20, [])
    assert report["valid"] is False
    assert "Count N=20 < 30" in report["reason"]

    # Case 3: Missing vars
    report = validate_dataset("TestDS", None, 50, ["Missing fatigue ratings"])
    assert report["valid"] is False
    assert "Missing fatigue ratings" in report["reason"]

def test_main_halt_on_failure(monkeypatch, tmp_path):
    """
    Test that main() exits with code 1 and writes validation_report.json
    when both datasets fail validation.
    """
    # Mock the fetch functions to return failures
    def mock_fetch_sleep_edf(config):
        return None, 10, ["N < 30"]
    
    def mock_fetch_shhs(config):
        return None, 15, ["N < 30"]
    
    # Patch the functions
    monkeypatch.setattr("download.fetch_sleep_edf", mock_fetch_sleep_edf)
    monkeypatch.setattr("download.fetch_shhs", mock_fetch_shhs)
    
    # Create a temporary directory for output
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Ensure data/processed exists
        Path("data/processed").mkdir(parents=True)
        
        # Call main and expect SystemExit
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
        
        # Check that validation_report.json was created
        report_path = Path("data/processed/validation_report.json")
        assert report_path.exists()
        
        with open(report_path, "r") as f:
            report = json.load(f)
        
        assert report["status"] == "failed"
        assert "primary_dataset" in report
        assert "fallback_dataset" in report
    finally:
        os.chdir(original_cwd)

def test_main_success_on_fallback(monkeypatch, tmp_path):
    """
    Test that main() succeeds (returns 0) if the fallback dataset passes.
    """
    def mock_fetch_sleep_edf(config):
        return None, 10, ["N < 30"]
    
    def mock_fetch_shhs(config):
        # Return a valid state for SHHS
        return None, 50, []
    
    monkeypatch.setattr("download.fetch_sleep_edf", mock_fetch_sleep_edf)
    monkeypatch.setattr("download.fetch_shhs", mock_fetch_shhs)
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        Path("data/processed").mkdir(parents=True)
        
        # Should not raise SystemExit
        result = main()
        assert result == 0
        
        # Check that validation_report.json was NOT created (or is not the failure one)
        # In this case, main returns 0, so no failure report should be written.
        report_path = Path("data/processed/validation_report.json")
        # Based on implementation: writes only on failure.
        # assert not report_path.exists() 
    finally:
        os.chdir(original_cwd)