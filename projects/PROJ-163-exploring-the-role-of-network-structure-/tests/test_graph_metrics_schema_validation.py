"""
Tests for the graph metrics schema validation logic.
"""
import os
import csv
import json
import tempfile
import pytest
from pathlib import Path

# Import the functions to test (assuming they are in validate_graph_metrics_schema.py)
# We will mock the file system interactions for unit testing
from validate_graph_metrics_schema import load_schema, load_csv_as_records, validate_records

@pytest.fixture
def valid_schema():
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "device_id": {"type": "string"},
            "metric_name": {"type": "string"},
            "value": {"type": "number"},
            "is_finite": {"type": "boolean"}
        },
        "required": ["device_id", "metric_name", "value", "is_finite"]
    }

@pytest.fixture
def valid_records():
    return [
        {"device_id": "ibmq_manila", "metric_name": "diameter", "value": 5.0, "is_finite": True},
        {"device_id": "ibmq_quito", "metric_name": "clustering", "value": 0.12, "is_finite": True},
        {"device_id": "ibm_brisbane", "metric_name": "path_length", "value": float('inf'), "is_finite": False}
    ]

@pytest.fixture
def invalid_records():
    return [
        {"device_id": "ibmq_manila", "metric_name": "diameter", "value": "not_a_number", "is_finite": True}, # value should be number
        {"device_id": "ibmq_quito", "metric_name": "clustering", "value": 0.12} # missing is_finite
    ]

def test_load_schema(tmp_path, valid_schema):
    schema_file = tmp_path / "test_schema.yaml"
    # Write valid JSON/YAML content
    import yaml
    with open(schema_file, 'w') as f:
        yaml.dump(valid_schema, f)
    
    loaded = load_schema(schema_file)
    assert loaded["type"] == "object"
    assert "device_id" in loaded["properties"]

def test_load_csv_as_records(tmp_path, valid_records):
    csv_file = tmp_path / "test_metrics.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["device_id", "metric_name", "value", "is_finite"])
        writer.writeheader()
        for r in valid_records:
            writer.writerow({
                "device_id": r["device_id"],
                "metric_name": r["metric_name"],
                "value": str(r["value"]),
                "is_finite": str(r["is_finite"]).lower()
            })
    
    loaded = load_csv_as_records(csv_file)
    assert len(loaded) == len(valid_records)
    assert loaded[0]["device_id"] == "ibmq_manila"
    assert isinstance(loaded[0]["value"], float)
    assert isinstance(loaded[0]["is_finite"], bool)

def test_validate_records_valid(valid_schema, valid_records):
    assert validate_records(valid_records, valid_schema) is True

def test_validate_records_invalid(valid_schema, invalid_records):
    assert validate_records(invalid_records, valid_schema) is False

def test_validate_records_missing_required(valid_schema):
    records = [{"device_id": "test", "metric_name": "test"}] # missing value, is_finite
    assert validate_records(records, valid_schema) is False

def test_validate_records_wrong_type(valid_schema):
    records = [{"device_id": 123, "metric_name": "test", "value": 1.0, "is_finite": True}] # device_id should be string
    assert validate_records(records, valid_schema) is False
