"""
Test for T039: Verify schema_check.csv structure and types.
This test ensures the CI smoke test data file exists and matches the
expected schema defined in FR-001, FR-006, and FR-007.
"""
import csv
import os
import pytest
from pathlib import Path

# Expected columns as per FR-001
EXPECTED_COLUMNS = [
    "MEQ_score",
    "MFQ_care",
    "MFQ_fairness",
    "MFQ_loyalty",
    "MFQ_authority",
    "MFQ_sanctity",
    "PSQI",
    "age",
    "sex",
    "acute_sleepiness"
]

# Expected row count (header + 1 data row)
EXPECTED_ROW_COUNT = 2

def get_test_data_path():
    """Get the path to the schema_check.csv file."""
    return Path(__file__).parent / "testdata" / "schema_check.csv"

def test_schema_check_file_exists():
    """Verify the schema_check.csv file exists."""
    path = get_test_data_path()
    assert path.exists(), f"Schema check file not found at {path}"

def test_schema_check_header():
    """Verify the CSV has the correct header columns."""
    path = get_test_data_path()
    with open(path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == EXPECTED_COLUMNS, (
            f"Header mismatch. Expected: {EXPECTED_COLUMNS}, Got: {header}"
        )

def test_schema_check_row_count():
    """Verify the CSV has exactly 2 rows (header + 1 data)."""
    path = get_test_data_path()
    with open(path, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == EXPECTED_ROW_COUNT, (
            f"Row count mismatch. Expected: {EXPECTED_ROW_COUNT}, Got: {len(rows)}"
        )

def test_schema_check_data_types():
    """Verify the single data row contains valid types (numeric/char)."""
    path = get_test_data_path()
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        row = next(reader)

        # Check numeric fields can be cast to float
        numeric_fields = [
            "MEQ_score", "MFQ_care", "MFQ_fairness", "MFQ_loyalty",
            "MFQ_authority", "MFQ_sanctity", "PSQI", "age", "acute_sleepiness"
        ]
        for field in numeric_fields:
            try:
                float(row[field])
            except ValueError:
                pytest.fail(f"Field '{field}' is not a valid number: {row[field]}")

        # Check sex is a character string (non-empty)
        assert isinstance(row["sex"], str) and len(row["sex"]) > 0, (
            f"Field 'sex' is not a valid string: {row['sex']}"
        )

def test_schema_check_no_synthetic_values():
    """
    Verify the data row does not contain obvious placeholder/synthetic values
    like 'NA', 'null', 'undefined', or empty strings in numeric fields.
    """
    path = get_test_data_path()
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        row = next(reader)

        invalid_values = {"NA", "null", "undefined", "nan", "N/A", ""}
        for key, value in row.items():
            if value.lower() in invalid_values:
                pytest.fail(
                    f"Field '{key}' contains invalid/synthetic placeholder value: '{value}'"
                )
