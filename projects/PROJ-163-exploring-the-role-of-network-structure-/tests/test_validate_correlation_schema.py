"""
Tests for the correlation results schema validation logic.
"""
import os
import csv
import json
import tempfile
import pytest
from pathlib import Path

# Mock jsonschema and yaml if not present, but assume they are for the actual run
try:
    import jsonschema
    import yaml
except ImportError:
    pytest.skip("jsonschema or yaml not installed", allow_module_level=True)

# Import the module under test
# We need to adjust the import path if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_correlation_results_schema import (
    load_schema,
    load_csv_as_records,
    validate_records
)

@pytest.fixture
def valid_schema():
    return {
        "type": "object",
        "properties": {
            "metric_a": {"type": "string"},
            "metric_b": {"type": "string"},
            "rho": {"type": "number"},
            "p_value": {"type": "number"},
            "adj_p_value": {"type": "number"}
        },
        "required": ["metric_a", "metric_b", "rho", "p_value", "adj_p_value"]
    }

@pytest.fixture
def valid_records():
    return [
        {
            "metric_a": "diameter",
            "metric_b": "t1_mean",
            "rho": -0.45,
            "p_value": 0.03,
            "adj_p_value": 0.05
        },
        {
            "metric_a": "clustering",
            "metric_b": "cx_error_mean",
            "rho": 0.12,
            "p_value": 0.45,
            "adj_p_value": 0.60
        }
    ]

@pytest.fixture
def invalid_records():
    return [
        {
            "metric_a": "diameter",
            "metric_b": "t1_mean",
            "rho": "not_a_number",  # Should be number
            "p_value": 0.03,
            "adj_p_value": 0.05
        }
    ]

@pytest.fixture
def missing_field_records():
    return [
        {
            "metric_a": "diameter",
            "metric_b": "t1_mean",
            "rho": -0.45,
            "p_value": 0.03
            # missing adj_p_value
        }
    ]

def test_load_schema(tmp_path, valid_schema):
    schema_file = tmp_path / "test_schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(valid_schema, f)
    
    loaded = load_schema(schema_file)
    assert loaded == valid_schema

def test_load_csv_as_records_valid(tmp_path, valid_records):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=valid_records[0].keys())
        writer.writeheader()
        writer.writerows(valid_records)
    
    records = load_csv_as_records(csv_file)
    assert len(records) == 2
    assert isinstance(records[0]['rho'], float)
    assert records[0]['metric_a'] == "diameter"

def test_load_csv_as_records_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_csv_as_records(tmp_path / "nonexistent.csv")

def test_validate_records_valid(valid_schema, valid_records):
    assert validate_records(valid_records, valid_schema) is True

def test_validate_records_invalid_type(valid_schema, invalid_records):
    assert validate_records(invalid_records, valid_schema) is False

def test_validate_records_missing_required(valid_schema, missing_field_records):
    assert validate_records(missing_field_records, valid_schema) is False

def test_validate_records_empty_list(valid_schema):
    assert validate_records([], valid_schema) is True
