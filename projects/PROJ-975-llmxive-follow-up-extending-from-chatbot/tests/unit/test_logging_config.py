import os
import json
import csv
import pytest
import logging

# Ensure we are in the project root context
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from code.logging_config import get_logger, log_experiment_entry, verify_log_file_exists, LOG_COLUMNS, CSVLogHandler

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path for testing."""
    log_dir = tmp_path / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "test_log.csv"
    return str(log_file)

def test_csv_handler_writes_header(temp_log_file):
    """Test that the CSV handler writes the header row exactly once."""
    handler = CSVLogHandler(temp_log_file)
    logger = logging.getLogger(f"test_{os.getpid()}")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # First log
    entry = {
        "task_id": "T001",
        "skill_id": "S1",
        "success": True,
        "latency": 0.5,
        "tokens": 100,
        "retrieval_precision": 1.0,
        "retrieval_diversity": 0.9,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": False,
        "edge_case": False
    }
    logger.info(json.dumps(entry))

    # Verify file content
    with open(temp_log_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
    assert len(rows) == 2, f"Expected header + 1 row, got {len(rows)}"
    assert rows[0] == LOG_COLUMNS, f"Header mismatch: {rows[0]} vs {LOG_COLUMNS}"
    
    # Second log
    entry["task_id"] = "T002"
    logger.info(json.dumps(entry))

    with open(temp_log_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
    assert len(rows) == 3, f"Expected header + 2 rows, got {len(rows)}"
    assert rows[2][0] == "T002"

def test_get_logger_singleton():
    """Test that get_logger returns the same instance."""
    logger1 = get_logger()
    logger2 = get_logger()
    assert logger1 is logger2

def test_log_experiment_entry_writes_file(tmp_path):
    """Test that log_experiment_entry writes to the expected file path."""
    # Temporarily override the global log path for this test
    import code.logging_config as lg
    original_path = lg._log_path
    lg._log_path = None # Reset to force re-init with new path if needed, but get_logger uses hardcoded path
    
    # We need to test the actual behavior which writes to data/results/experiment_log.csv
    # For unit testing, we can't easily change the hardcoded path without refactoring.
    # Instead, we test the verification function on a mock scenario or rely on integration.
    # However, we can test the logic by creating the directory and checking existence after a fake call.
    
    # Let's just test that the function doesn't crash and creates the file structure
    # We will use a temporary directory structure to mimic the expected path
    test_log_dir = tmp_path / "data" / "results"
    test_log_dir.mkdir(parents=True, exist_ok=True)
    test_log_file = str(test_log_dir / "experiment_log.csv")
    
    # Monkey patch the path for this test
    lg._log_path = test_log_file
    lg._logger = None
    lg._handler = None
    
    entry = {
        "task_id": "TEST",
        "skill_id": "S_TEST",
        "success": True,
        "latency": 0.1,
        "tokens": 50,
        "retrieval_precision": 0.8,
        "retrieval_diversity": 0.5,
        "pruning_risk_count": 0,
        "library_size": 20,
        "pruning_enabled": True,
        "edge_case": False
    }
    
    log_experiment_entry(entry)
    
    assert os.path.exists(test_log_file), "Log file was not created"
    assert verify_log_file_exists(), "File exists but is empty"
    
    # Restore
    lg._log_path = original_path
    lg._logger = None
    lg._handler = None

def test_schema_columns_match():
    """Verify that LOG_COLUMNS matches the schema properties."""
    expected_cols = [
        "task_id", "skill_id", "success", "latency", "tokens",
        "retrieval_precision", "retrieval_diversity", "pruning_risk_count",
        "library_size", "pruning_enabled", "edge_case"
    ]
    assert LOG_COLUMNS == expected_cols, "LOG_COLUMNS does not match schema properties"
