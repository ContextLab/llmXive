"""
Unit tests for Task T017b: Markov State Validation.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to import the functions from run_t017b
# Since run_t017b imports from config, we need to ensure the environment is set up
# or mock the config functions.

# Mocking config functions to avoid dependency on actual project structure in tests
@pytest.fixture
def mock_config_paths(tmp_path):
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    analysis_dir = tmp_path / "analysis"
    
    data_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    analysis_dir.mkdir(parents=True)

    # Patch the config functions
    with patch("run_t017b.get_data_dir", return_value=data_dir), \
         patch("run_t017b.get_processed_dir", return_value=processed_dir):
         yield {
             "data_dir": data_dir,
             "processed_dir": processed_dir,
             "analysis_dir": analysis_dir
         }

def test_validate_markov_state_file_not_found(mock_config_paths):
    from run_t017b import validate_markov_state
    
    # Ensure the file does not exist
    markov_path = mock_config_paths["processed_dir"] / "markov_state.json"
    assert not markov_path.exists()

    result = validate_markov_state()
    assert result is False

def test_validate_markov_state_invalid_json(mock_config_paths):
    from run_t017b import validate_markov_state
    
    markov_path = mock_config_paths["processed_dir"] / "markov_state.json"
    markov_path.write_text("not valid json {")

    result = validate_markov_state()
    assert result is False

def test_validate_markov_state_missing_order(mock_config_paths):
    from run_t017b import validate_markov_state
    
    markov_path = mock_config_paths["processed_dir"] / "markov_state.json"
    markov_path.write_text(json.dumps({"transition_matrix": {}}))

    result = validate_markov_state()
    assert result is False

def test_validate_markov_state_wrong_order(mock_config_paths):
    from run_t017b import validate_markov_state
    
    markov_path = mock_config_paths["processed_dir"] / "markov_state.json"
    markov_path.write_text(json.dumps({"order": 2, "transition_matrix": {}}))

    result = validate_markov_state()
    assert result is False

def test_validate_markov_state_success(mock_config_paths):
    from run_t017b import validate_markov_state
    
    markov_path = mock_config_paths["processed_dir"] / "markov_state.json"
    markov_path.write_text(json.dumps({"order": 1, "transition_matrix": {}}))

    result = validate_markov_state()
    assert result is True

def test_run_t017b_updates_log_success(mock_config_paths):
    from run_t017b import run, load_verification_log, get_verification_log_path
    
    # Create valid markov file
    markov_path = mock_config_paths["processed_dir"] / "markov_state.json"
    markov_path.write_text(json.dumps({"order": 1}))

    # Run
    success = run()
    assert success is True

    # Check log
    log_path = get_verification_log_path()
    assert log_path.exists()
    
    log_data = load_verification_log()
    assert "T017b" in log_data
    assert log_data["T017b"]["status"] == "passed"

def test_run_t017b_updates_log_failure(mock_config_paths):
    from run_t017b import run, load_verification_log, get_verification_log_path
    
    # Create invalid markov file (wrong order)
    markov_path = mock_config_paths["processed_dir"] / "markov_state.json"
    markov_path.write_text(json.dumps({"order": 0}))

    # Run
    success = run()
    assert success is False

    # Check log
    log_path = get_verification_log_path()
    assert log_path.exists()
    
    log_data = load_verification_log()
    assert "T017b" in log_data
    assert log_data["T017b"]["status"] == "failed"
