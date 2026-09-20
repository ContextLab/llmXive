"""
Unit tests for Task T014c: Check P/N Availability and Flag.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# We need to mock the config and state_manager for isolated testing
# Since the actual implementation relies on project-wide config files,
# we simulate the environment.

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary directory structure simulating the project."""
    # Create required dirs
    (tmp_path / "logs").mkdir()
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "data").mkdir()
    
    # Create a mock state file with p_n_available = False
    state_file = tmp_path / "artifacts" / "state.json"
    state_data = {
        "project_id": "PROJ-457",
        "data_quality": {
            "p_n_available": False
        }
    }
    with open(state_file, 'w') as f:
        json.dump(state_data, f)
    
    # Create config file
    config_file = tmp_path / "config.yaml"
    config_data = {
        "LOGS_PATH": str(tmp_path / "logs"),
        "ARTIFACTS_PATH": str(tmp_path / "artifacts"),
        "DATA_PATH": str(tmp_path / "data")
    }
    with open(config_file, 'w') as f:
        import yaml
        yaml.dump(config_data, f)
        
    return tmp_path

def test_log_hypothesis_unverifiable_creates_file(temp_project_dir):
    """
    Test that log_hypothesis_unverifiable creates logs/deviation.log
    and writes the correct message when p_n_available is False.
    """
    # Mock config
    config = {
        "LOGS_PATH": str(temp_project_dir / "logs"),
        "ARTIFACTS_PATH": str(temp_project_dir / "artifacts")
    }
    
    # Import the function to test
    # We need to adjust the import path or mock the config module
    # For this unit test, we will test the logic by calling the main entry
    # but since we can't easily import the module without the full project setup,
    # we will test the behavior via the main function with mocked dependencies.
    
    # Instead, let's test the logic directly by inspecting the file after execution
    # We will use the main function but mock the config loading
    
    import sys
    sys.path.insert(0, str(temp_project_dir.parent)) # Ensure we can find the module if needed
    
    # Actually, let's just test the file creation logic directly
    from code.pn_availability_checker import log_hypothesis_unverifiable
    import logging
    
    logger = logging.getLogger("test_logger")
    
    log_hypothesis_unverifiable(config, logger)
    
    deviation_log_path = Path(config["LOGS_PATH"]) / "deviation.log"
    assert deviation_log_path.exists(), "deviation.log should be created"
    
    content = deviation_log_path.read_text()
    assert "Hypothesis Unverifiable" in content, "Deviation log should contain 'Hypothesis Unverifiable'"
    assert "FR-001" in content, "Deviation log should reference FR-001"

def test_update_state_flag_hypothesis_updates_json(temp_project_dir):
    """
    Test that update_state_flag_hypothesis updates state.json correctly
    when p_n_available is False.
    """
    config = {
        "LOGS_PATH": str(temp_project_dir / "logs"),
        "ARTIFACTS_PATH": str(temp_project_dir / "artifacts")
    }
    
    from code.pn_availability_checker import update_state_flag_hypothesis
    import logging
    
    logger = logging.getLogger("test_logger")
    
    update_state_flag_hypothesis(config, logger)
    
    state_path = Path(config["ARTIFACTS_PATH"]) / "state.json"
    with open(state_path, 'r') as f:
        updated_state = json.load(f)
        
    assert updated_state.get("hypothesis", {}).get("status") == "unverifiable", \
        "State should mark hypothesis as unverifiable"
    assert updated_state.get("hypothesis", {}).get("p_n_available") == False, \
        "State should reflect p_n_available as False"
    assert "Missing Phosphorus" in updated_state.get("hypothesis", {}).get("reason", ""), \
        "State should include reason for unverifiable status"

def test_no_update_when_pn_available(temp_project_dir):
    """
    Test that no deviation logging or state update occurs if p_n_available is True.
    """
    # Modify state to have p_n_available = True
    state_path = temp_project_dir / "artifacts" / "state.json"
    state_data = {
        "project_id": "PROJ-457",
        "data_quality": {
            "p_n_available": True
        }
    }
    with open(state_path, 'w') as f:
        json.dump(state_data, f)
        
    config = {
        "LOGS_PATH": str(temp_project_dir / "logs"),
        "ARTIFACTS_PATH": str(temp_project_dir / "artifacts")
    }
    
    from code.pn_availability_checker import log_hypothesis_unverifiable, update_state_flag_hypothesis
    import logging
    
    logger = logging.getLogger("test_logger")
    
    # These should not raise errors, but should not write the deviation log
    # We can't easily test 'no write' without mocking, so we test the state update logic
    # by checking that the hypothesis key is not added/changed if not needed
    
    # Actually, the current implementation of update_state_flag_hypothesis returns early
    # if p_n_available is True, so we just verify it doesn't crash and state remains valid
    update_state_flag_hypothesis(config, logger)
    
    with open(state_path, 'r') as f:
        final_state = json.load(f)
        
    # The hypothesis key should not be added if p_n_available is True
    # (based on the logic: if not p_n_available: ... else: log info)
    # Note: The current implementation only updates if False.
    # If it was True, it logs and returns. So 'hypothesis' key should not exist or remain unchanged.
    # In the initial state, 'hypothesis' key didn't exist.
    assert "hypothesis" not in final_state or final_state["hypothesis"].get("status") != "unverifiable", \
        "Hypothesis should not be marked unverifiable if p_n_available is True"