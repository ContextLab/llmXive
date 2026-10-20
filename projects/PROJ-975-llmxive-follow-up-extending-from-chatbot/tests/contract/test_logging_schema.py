import os
import yaml
import csv
import pytest
from jsonschema import validate
from code.logging_config import get_logger, log_experiment_entry
from llmxive_toolkit import paths

SCHEMA_PATH = "contracts/experiment_log.schema.yaml"
LOG_PATH = str(paths.data("results", "experiment_log.csv"))

def load_schema():
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test_logging_csv_schema_compliance():
    """
    Verifies that the CSV produced by the logger conforms to the experiment_log.schema.yaml.
    """
    schema = load_schema()
    
    # To ensure we are testing the current implementation and not a stale file,
    # we write a fresh entry.
    test_entry = {
        "task_id": "test_schema_001",
        "skill_id": "skill_test",
        "success": True,
        "latency": 0.05,
        "tokens": 10,
        "retrieval_precision": 0.5,
        "retrieval_diversity": 0.5,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": True,
        "edge_case": False
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
        
        # Cast types for jsonschema validation (CSV is all strings)
        # We must handle cases where values might be empty strings
        def to_bool(v): return v.lower() == 'true'
        def to_float(v): return float(v) if v else 0.0
        def to_int(v): return int(v) if v else 0
        
        casted_row = {
            "task_id": row_dict.get("task_id", ""),
            "skill_id": row_dict.get("skill_id", ""),
            "success": to_bool(row_dict.get("success", "false")),
            "latency": to_float(row_dict.get("latency", "0")),
            "tokens": to_int(row_dict.get("tokens", "0")),
            "retrieval_precision": to_float(row_dict.get("retrieval_precision", "0")),
            "retrieval_diversity": to_float(row_dict.get("retrieval_diversity", "0")),
            "pruning_risk_count": to_int(row_dict.get("pruning_risk_count", "0")),
            "library_size": to_int(row_dict.get("library_size", "0")),
            "pruning_enabled": to_bool(row_dict.get("pruning_enabled", "false")),
            "edge_case": to_bool(row_dict.get("edge_case", "false")),
        }
        
        validate(instance=casted_row, schema=schema)

def test_logger_singleton():
    """
    Ensures get_logger returns the same instance.
    """
    log1 = get_logger("test1")
    log2 = get_logger("test2")
    assert log1 is log2
