import os
import yaml
import csv
import pytest
from jsonschema import validate, ValidationError
from code.logging_config import get_logger, log_experiment_entry

SCHEMA_PATH = "contracts/experiment_log.schema.yaml"
LOG_PATH = "data/results/experiment_log.csv"

def load_schema():
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test_logging_csv_schema_compliance():
    """
    Verifies that the CSV produced by the logger conforms to the experiment_log.schema.yaml.
    """
    schema = load_schema()
    
    # Trigger a write
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
        header = lines[0].strip().split(',')
        last_row = lines[-1].strip().split(',')
        
        # Map CSV row to dictionary
        row_dict = dict(zip(header, last_row))
        
        # Cast types for jsonschema validation (CSV is all strings)
        casted_row = {
            "task_id": row_dict["task_id"],
            "skill_id": row_dict["skill_id"],
            "success": row_dict["success"].lower() == 'true',
            "latency": float(row_dict["latency"]),
            "tokens": int(row_dict["tokens"]),
            "retrieval_precision": float(row_dict["retrieval_precision"]),
            "retrieval_diversity": float(row_dict["retrieval_diversity"]),
            "pruning_risk_count": int(row_dict["pruning_risk_count"]),
            "library_size": int(row_dict["library_size"]),
            "pruning_enabled": row_dict["pruning_enabled"].lower() == 'true',
            "edge_case": row_dict["edge_case"].lower() == 'true',
        }
        
        validate(instance=casted_row, schema=schema)

def test_logger_singleton():
    """
    Ensures get_logger returns the same instance.
    """
    log1 = get_logger("test1")
    log2 = get_logger("test2")
    assert log1 is log2