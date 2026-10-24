import os
import yaml
import csv
import pytest
from jsonschema import validate
from code.logging_config import get_logger, log_experiment_entry, LOG_COLUMNS
from llmxive_toolkit import paths

SCHEMA_PATH = "contracts/experiment_log.schema.yaml"
LOG_PATH = str(paths.data("results", "experiment_log.csv"))

def load_schema():
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Ensure a clean log file before every test to avoid header pollution."""
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    yield

def test_logging_csv_header_order():
    """
    Verifies that the CSV header matches the required order in LOG_COLUMNS.
    """
    # Write a dummy entry to ensure header is created
    test_entry = {col: "test" for col in LOG_COLUMNS}
    log_experiment_entry(test_entry)
    
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        assert header == LOG_COLUMNS, f"Header mismatch. Expected {LOG_COLUMNS}, got {header}"

def test_logging_csv_schema_compliance():
    """
    Verifies that the CSV produced by the logger conforms to the experiment_log.schema.yaml.
    """
    schema = load_schema()
    
    # Write a fresh entry for validation
    test_entry = {
        "run_id": "run_001",
        "task_id": "task_001",
        "library_size": 50,
        "pruning_enabled": True,
        "success": True,
        "latency_ms": 120.5,
        "tokens_used": 450,
        "retrieval_precision": 0.8,
        "retrieval_diversity": 0.6,
        "edge_case": "none"
    }
    log_experiment_entry(test_entry)
    
    # Read the last line of the CSV
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if not lines:
            pytest.fail("Log file is empty")
        
        header = lines[0].strip().split(',')
        last_row = lines[-1].strip().split(',')
        
        # Map CSV row to dictionary
        row_dict = dict(zip(header, last_row))
        
        # Cast types for jsonschema validation
        def to_bool(v): return v.lower() == 'true'
        def to_float(v): return float(v) if v else 0.0
        def to_int(v): return int(v) if v else 0
        
        casted_row = {
            "run_id": row_dict.get("run_id", ""),
            "task_id": row_dict.get("task_id", ""),
            "library_size": to_int(row_dict.get("library_size", "0")),
            "pruning_enabled": to_bool(row_dict.get("pruning_enabled", "false")),
            "success": to_bool(row_dict.get("success", "false")),
            "latency_ms": to_float(row_dict.get("latency_ms", "0")),
            "tokens_used": to_int(row_dict.get("tokens_used", "0")),
            "retrieval_precision": to_float(row_dict.get("retrieval_precision", "0")),
            "retrieval_diversity": to_float(row_dict.get("retrieval_diversity", "0")),
            "edge_case": row_dict.get("edge_case", ""),
        }
        
        validate(instance=casted_row, schema=schema)

def test_logger_singleton():
    """
    Ensures get_logger returns the same instance.
    """
    log1 = get_logger("test1")
    log2 = get_logger("test2")
    assert log1 is log2