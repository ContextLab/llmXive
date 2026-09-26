import os
import csv
import json
import pytest
from pathlib import Path
import sys

# Ensure parent is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from contracts.schema_validators import validate_subject_metrics_schema

@pytest.fixture
def valid_csv_path(tmp_path):
    """Create a valid subject_metrics.csv in tmp_path."""
    path = tmp_path / "subject_metrics.csv"
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "subject_id", "flexibility_DMN", "flexibility_Salience", "flexibility_Hippocampal",
            "stability_DMN", "stability_Salience", "stability_Hippocampal"
        ])
        writer.writerow(["sub-01", 0.5, 0.6, 0.4, 10.0, 12.0, 8.0])
        writer.writerow(["sub-02", 0.55, 0.65, 0.45, 11.0, 13.0, 9.0])
    return path

@pytest.fixture
def missing_column_csv_path(tmp_path):
    """Create a CSV with a missing required column."""
    path = tmp_path / "subject_metrics_missing.csv"
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["subject_id", "flexibility_DMN"])
        writer.writerow(["sub-01", 0.5])
    return path

@pytest.fixture
def invalid_type_csv_path(tmp_path):
    """Create a CSV with invalid data types."""
    path = tmp_path / "subject_metrics_invalid.csv"
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "subject_id", "flexibility_DMN", "flexibility_Salience", "flexibility_Hippocampal",
            "stability_DMN", "stability_Salience", "stability_Hippocampal"
        ])
        writer.writerow(["sub-01", "not_a_number", 0.6, 0.4, 10.0, 12.0, 8.0])
    return path

def test_valid_schema(valid_csv_path):
    """Test that a correctly formatted CSV passes validation."""
    assert validate_subject_metrics_schema(str(valid_csv_path)) is True

def test_missing_column_fails(missing_column_csv_path):
    """Test that a CSV with missing columns fails validation."""
    assert validate_subject_metrics_schema(str(missing_column_csv_path)) is False

def test_invalid_type_fails(invalid_type_csv_path):
    """Test that a CSV with invalid data types fails validation."""
    # Note: Depending on strictness of validator, this might pass if it only checks headers.
    # If the validator checks types, this should fail.
    # For this test, we assume the validator is robust enough to catch type errors.
    # If the current validator only checks headers, we might need to adjust the test
    # or the validator implementation.
    result = validate_subject_metrics_schema(str(invalid_type_csv_path))
    # We assert False here to indicate that if the validator doesn't catch types,
    # the test fails (meaning the validator is incomplete).
    # However, if the task only requires header validation, this might be True.
    # Given the requirement "JSON/CSV validation", type checking is implied.
    assert result is False, "Validator should reject non-numeric values in numeric columns"
