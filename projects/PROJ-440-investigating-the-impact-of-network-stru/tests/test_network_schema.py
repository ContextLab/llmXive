"""
Tests for the Network Schema and Validator.
"""
import pytest
import tempfile
import os
import csv
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.network_schema_loader import load_schema, validate_csv_against_schema, _validate_row_against_schema


@pytest.fixture
def valid_row():
    return {
        "id": "graph_123",
        "class": "random",
        "N": "100",
        "clustering_coeff": "0.45",
        "avg_path_length": "3.2",
        "degree_dist_summary": '{"mean": 4.5, "max": 8}',
        "mean_degree": "4.5",
        "max_degree": "8",
        "min_degree": "2",
        "degree_std": "1.2",
        "theoretical_match": "passed",
        "generation_seed": "42"
    }

@pytest.fixture
def schema():
    return load_schema()


def test_load_schema_success(schema):
    assert "properties" in schema
    assert "required" in schema
    assert "id" in schema["properties"]
    assert "class" in schema["properties"]


def test_validate_row_valid(valid_row, schema):
    is_valid, msg = _validate_row_against_schema(valid_row, schema)
    assert is_valid
    assert msg == ""


def test_validate_row_missing_field(valid_row, schema):
    del valid_row["id"]
    is_valid, msg = _validate_row_against_schema(valid_row, schema)
    assert not is_valid
    assert "Missing required fields" in msg


def test_validate_row_invalid_class(valid_row, schema):
    valid_row["class"] = "invalid_class"
    is_valid, msg = _validate_row_against_schema(valid_row, schema)
    assert not is_valid
    assert "not in enum" in msg


def test_validate_row_invalid_n(valid_row, schema):
    valid_row["N"] = "5" # Below minimum 10
    is_valid, msg = _validate_row_against_schema(valid_row, schema)
    assert not is_valid
    assert "below minimum" in msg


def test_validate_row_negative_clustering(valid_row, schema):
    valid_row["clustering_coeff"] = "-0.1"
    is_valid, msg = _validate_row_against_schema(valid_row, schema)
    assert not is_valid
    assert "below minimum" in msg


def test_validate_csv_valid(tmp_path, valid_row, schema):
    csv_file = tmp_path / "test_networks.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=valid_row.keys())
        writer.writeheader()
        writer.writerow(valid_row)

    is_valid, errors = validate_csv_against_schema(csv_file, schema)
    assert is_valid
    assert len(errors) == 0


def test_validate_csv_invalid(tmp_path, valid_row, schema):
    # Modify a row to be invalid
    invalid_row = valid_row.copy()
    invalid_row["class"] = "invalid"

    csv_file = tmp_path / "test_networks_invalid.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=invalid_row.keys())
        writer.writeheader()
        writer.writerow(valid_row)
        writer.writerow(invalid_row)

    is_valid, errors = validate_csv_against_schema(csv_file, schema)
    assert not is_valid
    assert len(errors) > 0
    assert any("invalid" in e.lower() for e in errors)


def test_validate_csv_missing_file(schema):
    is_valid, errors = validate_csv_against_schema(Path("/nonexistent/file.csv"), schema)
    assert not is_valid
    assert "not found" in errors[0].lower()