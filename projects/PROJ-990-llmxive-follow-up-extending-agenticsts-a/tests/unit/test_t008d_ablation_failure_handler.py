import os
import json
import pytest
from pathlib import Path
import logging
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from t008d_ablation_failure_handler import (
    check_ablation_success, 
    log_critical_failure, 
    generate_fallback_flag, 
    main,
    ABLATION_LABELS_PATH,
    FALLBACK_FLAG_PATH,
    EDGE_CASE_LOG_PATH
)

@pytest.fixture
def temp_files(tmp_path):
    """Set up temporary paths for testing."""
    # Create a temporary directory structure
    data_processed = tmp_path / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)
    
    # Mock the global paths to use tmp_path
    original_ablation_path = ABLATION_LABELS_PATH
    original_fallback_path = FALLBACK_FLAG_PATH
    original_log_path = EDGE_CASE_LOG_PATH
    
    # We will use monkeypatch in the tests to swap these, 
    # but for simplicity in this fixture, we just ensure the dir exists.
    return {
        "processed_dir": data_processed,
        "ablation_file": data_processed / "ablation_labels_train.json",
        "fallback_file": data_processed / "fallback_flag.json",
        "log_file": data_processed / "edge_case_warnings.log"
    }

def test_check_ablation_success_file_missing(temp_files, tmp_path, monkeypatch):
    """Test that check_ablation_success returns False when file is missing."""
    # Ensure the file does not exist
    if temp_files["ablation_file"].exists():
        temp_files["ablation_file"].unlink()
    
    # Monkeypatch the global path
    monkeypatch.setattr("t008d_ablation_handler.ABLATION_LABELS_PATH", temp_files["ablation_file"])
    
    # We need to re-import or reload the module to pick up the monkeypatched path
    # Since the function uses the global constant directly, we patch the module's attribute
    with patch('t008d_ablation_failure_handler.ABLATION_LABELS_PATH', temp_files["ablation_file"]):
        result = check_ablation_success()
        assert result is False

def test_check_ablation_success_empty_file(temp_files, tmp_path, monkeypatch):
    """Test that check_ablation_success returns False when file is empty."""
    # Create empty file
    temp_files["ablation_file"].write_text("")
    
    with patch('t008d_ablation_failure_handler.ABLATION_LABELS_PATH', temp_files["ablation_file"]):
        result = check_ablation_success()
        assert result is False

def test_check_ablation_success_invalid_json(temp_files, tmp_path, monkeypatch):
    """Test that check_ablation_success returns False when file has invalid JSON."""
    temp_files["ablation_file"].write_text("{ invalid json }")
    
    with patch('t008d_ablation_failure_handler.ABLATION_LABELS_PATH', temp_files["ablation_file"]):
        result = check_ablation_success()
        assert result is False

def test_check_ablation_success_valid_data(temp_files, tmp_path, monkeypatch):
    """Test that check_ablation_success returns True when file has valid data."""
    valid_data = {"layer_1": 0.5, "layer_2": 0.8}
    temp_files["ablation_file"].write_text(json.dumps(valid_data))
    
    with patch('t008d_ablation_failure_handler.ABLATION_LABELS_PATH', temp_files["ablation_file"]):
        result = check_ablation_success()
        assert result is True

def test_generate_fallback_flag_creates_file(temp_files, tmp_path, monkeypatch):
    """Test that generate_fallback_flag creates the correct JSON file."""
    reason = "Test failure"
    
    with patch('t008d_ablation_failure_handler.FALLBACK_FLAG_PATH', temp_files["fallback_file"]):
        generate_fallback_flag(reason)
        
        assert temp_files["fallback_file"].exists()
        content = json.loads(temp_files["fallback_file"].read_text())
        
        assert content["fallback"] is True
        assert content["use_heuristic"] is True
        assert content["reason"] == reason
        assert "timestamp" in content
        assert "heuristic_params" in content
        assert content["heuristic_params"]["k"] == 2

def test_log_critical_failure_writes_to_log(temp_files, tmp_path, monkeypatch):
    """Test that log_critical_failure writes to the log file."""
    reason = "Test critical error"
    
    with patch('t008d_ablation_failure_handler.EDGE_CASE_LOG_PATH', temp_files["log_file"]):
        log_critical_failure(reason)
        
        assert temp_files["log_file"].exists()
        log_content = temp_files["log_file"].read_text()
        assert "[CRITICAL]" in log_content
        assert reason in log_content

def test_main_triggers_fallback_when_ablation_missing(temp_files, tmp_path, monkeypatch, caplog):
    """Test that main() triggers fallback handling when ablation file is missing."""
    # Ensure ablation file is missing
    if temp_files["ablation_file"].exists():
        temp_files["ablation_file"].unlink()
    
    # Patch the paths
    with patch('t008d_ablation_failure_handler.ABLATION_LABELS_PATH', temp_files["ablation_file"]), \
         patch('t008d_ablation_failure_handler.FALLBACK_FLAG_PATH', temp_files["fallback_file"]), \
         patch('t008d_ablation_failure_handler.EDGE_CASE_LOG_PATH', temp_files["log_file"]):
        
        main()
        
        # Verify fallback flag was created
        assert temp_files["fallback_file"].exists()
        content = json.loads(temp_files["fallback_file"].read_text())
        assert content["fallback"] is True
        
        # Verify log was written
        assert temp_files["log_file"].exists()
        assert "[CRITICAL]" in temp_files["log_file"].read_text()

def test_main_no_action_when_ablation_success(temp_files, tmp_path, monkeypatch):
    """Test that main() does nothing when ablation file exists and is valid."""
    valid_data = {"layer_1": 0.9}
    temp_files["ablation_file"].write_text(json.dumps(valid_data))
    
    # Ensure fallback file does not exist initially
    if temp_files["fallback_file"].exists():
        temp_files["fallback_file"].unlink()
    
    with patch('t008d_ablation_failure_handler.ABLATION_LABELS_PATH', temp_files["ablation_file"]), \
         patch('t008d_ablation_failure_handler.FALLBACK_FLAG_PATH', temp_files["fallback_file"]), \
         patch('t008d_ablation_failure_handler.EDGE_CASE_LOG_PATH', temp_files["log_file"]):
        
        main()
        
        # Fallback file should NOT be created
        assert not temp_files["fallback_file"].exists()