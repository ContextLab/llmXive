import os
import json
import csv
import pytest
from code.logging_config import get_logger, log_experiment_entry, verify_log_file_exists, LOG_COLUMNS

@pytest.fixture
def clean_log_file(tmp_path):
    """Fixture to create a temporary log file path and clean up after test."""
    # We need to override the global path for testing, but since the module
    # uses a global variable, we will test in a way that doesn't interfere
    # with the actual project path if run in parallel, or we assume the test
    # runner handles isolation. For this task, we will verify the logic
    # by checking the file at the expected relative path or a temp path.
    # However, to strictly follow the constraint of writing to the project tree,
    # we will write to a temp directory but verify the logic works.
    # Actually, the requirement says "stay inside project tree". 
    # We will mock the path or ensure the test runs in isolation.
    # For this implementation, we will test the CSV generation logic 
    # by creating a temporary file and passing it to a modified handler if possible,
    # but since we cannot change the API easily, we will test the side effect
    # on a known path in the test directory or rely on the global state reset.
    
    # Simplest approach for this task: Create a test file in data/results
    # and clean it up.
    test_path = "data/results/test_experiment_log.csv"
    
    # Ensure directory exists
    os.makedirs("data/results", exist_ok=True)
    
    # Remove if exists
    if os.path.exists(test_path):
        os.remove(test_path)
        
    yield test_path
    
    if os.path.exists(test_path):
        os.remove(test_path)

def test_log_entry_creation(clean_log_file):
    """Test that a log entry is correctly written to CSV with headers."""
    # Note: The global logger in logging_config.py is hardcoded to "data/results/experiment_log.csv".
    # To test with the fixture path, we would need to refactor get_logger to accept a path
    # or patch the module. Given the constraint to not re-author, we will test the
    # functionality by writing to the default path and verifying the file content.
    
    # We will temporarily patch the global path in the module for this test
    import code.logging_config as lg_module
    original_path = lg_module._log_path
    lg_module._log_path = clean_log_file
    lg_module._logger = None # Reset logger to force re-init
    lg_module._handler = None

    try:
        logger = get_logger()
        test_entry = {
            "task_id": "T001",
            "skill_id": "S001",
            "success": True,
            "latency": 0.5,
            "tokens": 100,
            "retrieval_precision": 0.8,
            "retrieval_diversity": 0.2,
            "pruning_risk_count": 0,
            "library_size": 10,
            "pruning_enabled": False,
            "edge_case": False
        }
        
        log_experiment_entry(test_entry)
        
        # Verify file exists
        assert os.path.exists(clean_log_file), "Log file was not created"
        
        # Verify content
        with open(clean_log_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
            row = rows[0]
            
            # Check headers match schema
            assert list(row.keys()) == LOG_COLUMNS, f"Headers mismatch: {list(row.keys())}"
            
            # Check values
            assert row["task_id"] == "T001"
            assert row["success"] == "True" # CSV writes booleans as strings
            assert float(row["latency"]) == 0.5
    finally:
        # Restore
        lg_module._log_path = original_path
        lg_module._logger = None
        lg_module._handler = None

def test_log_schema_compliance(clean_log_file):
    """Test that the log entry strictly follows the schema columns."""
    import code.logging_config as lg_module
    lg_module._log_path = clean_log_file
    lg_module._logger = None
    lg_module._handler = None

    try:
        logger = get_logger()
        
        # Log an entry with missing optional fields (should default to empty)
        minimal_entry = {
            "task_id": "T002",
            "skill_id": "S002",
            "success": False
        }
        
        log_experiment_entry(minimal_entry)
        
        with open(clean_log_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            row = rows[0]
            
            # All columns must be present
            for col in LOG_COLUMNS:
                assert col in row, f"Missing column: {col}"
                
            # Check that missing fields are empty
            assert row["latency"] == ""
            assert row["tokens"] == ""
    finally:
        lg_module._log_path = None
        lg_module._logger = None
        lg_module._handler = None

def test_verify_log_file_exists(clean_log_file):
    """Test the verification function."""
    import code.logging_config as lg_module
    lg_module._log_path = clean_log_file
    lg_module._logger = None
    lg_module._handler = None

    try:
        # Before writing
        assert not verify_log_file_exists()
        
        log_experiment_entry({"task_id": "T003", "skill_id": "S003", "success": True})
        
        # After writing
        assert verify_log_file_exists()
    finally:
        lg_module._log_path = None
        lg_module._logger = None
        lg_module._handler = None
