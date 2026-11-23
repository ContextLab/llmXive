"""
Unit tests for T008d: Ablation Failure Handling.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from t008d_ablation_failure_handler import (
    check_ablation_success, 
    generate_fallback_flag, 
    log_critical_failure,
    DATA_PROCESSED,
    ABALATION_LABELS_PATH,
    FALLBACK_FLAG_PATH,
    WARN_LOG_PATH
)

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure mimicking the project root."""
    # We need to mock the global paths in the module.
    # Since the module uses Path.cwd() at import time, we change cwd for the test.
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    # Re-import to pick up new cwd (or manually patch the globals if preferred)
    # For simplicity in this test, we will rely on the fact that the functions
    # use global constants defined at module level which were set at import time.
    # To make this robust, we should patch the module's globals.
    
    # Actually, the module defines PROJECT_ROOT = Path.cwd() at import.
    # Since we imported it before changing cwd, we need to patch the constants.
    import t008d_ablation_failure_handler as handler_module
    handler_module.PROJECT_ROOT = tmp_path
    handler_module.DATA_PROCESSED = tmp_path / "data" / "processed"
    handler_module.ABALATION_LABELS_PATH = handler_module.DATA_PROCESSED / "ablation_labels_train.json"
    handler_module.FALLBACK_FLAG_PATH = handler_module.DATA_PROCESSED / "fallback_flag.json"
    handler_module.WARN_LOG_PATH = handler_module.DATA_PROCESSED / "edge_case_warnings.log"
    
    # Ensure directory exists
    handler_module.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    
    yield tmp_path
    
    os.chdir(original_cwd)

def test_check_ablation_success_missing_file(temp_project_root):
    """Test that check_ablation_success returns False when file is missing."""
    assert not check_ablation_success()

def test_check_ablation_success_empty_file(temp_project_root):
    """Test that check_ablation_success returns False when file is empty."""
    ABALATION_LABELS_PATH.touch()
    assert not check_ablation_success()

def test_check_ablation_success_invalid_json(temp_project_root):
    """Test that check_ablation_success returns False when file contains invalid JSON."""
    ABALATION_LABELS_PATH.write_text("not valid json")
    assert not check_ablation_success()

def test_check_ablation_success_valid_json(temp_project_root):
    """Test that check_ablation_success returns True when file contains valid JSON."""
    valid_data = {"labels": [1, 2, 3]}
    with open(ABALATION_LABELS_PATH, 'w') as f:
        json.dump(valid_data, f)
    assert check_ablation_success()

def test_generate_fallback_flag_creates_file(temp_project_root):
    """Test that generate_fallback_flag creates the correct JSON file."""
    result = generate_fallback_flag()
    
    assert FALLBACK_FLAG_PATH.exists()
    assert result["fallback"] is True
    assert result["use_heuristic"] is True
    assert result["reason"] == "Ablation study failed"
    assert "heuristic_config" in result
    assert result["heuristic_config"]["k"] == 2

def test_log_critical_failure_writes_to_log(temp_project_root):
    """Test that log_critical_failure writes a JSON line to the log file."""
    import logging
    logger = logging.getLogger("T008d_Handler")
    log_critical_failure(logger)
    
    assert WARN_LOG_PATH.exists()
    content = WARN_LOG_PATH.read_text()
    assert "CRITICAL" in content
    assert "Ablation study" in content
    # Verify it's valid JSON line
    try:
        json.loads(content.strip())
    except json.JSONDecodeError:
        pytest.fail("Log file content is not valid JSON")