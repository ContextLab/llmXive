"""
Contract test for merged dataset schema (data/processed/merged_data.csv).
Validates that the CSV output matches the schema defined in
specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml.
"""
import os
import csv
import json
import pytest
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_PATH = os.path.join(
    PROJECT_ROOT,
    "specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml"
)
DATA_PATH = os.path.join(PROJECT_ROOT, "data/processed/merged_data.csv")


def load_schema():
    """Load the dataset schema definition."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data():
    """Load the merged dataset."""
    if not os.path.exists(DATA_PATH):
        pytest.skip(f"Data file not found at {DATA_PATH}")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_schema_exists():
    """Verify the schema file exists and is valid YAML."""
    schema = load_schema()
    assert schema is not None
    assert "fields" in schema or "columns" in schema


def test_required_columns_present():
    """Verify all required columns from schema exist in the CSV."""
    schema = load_schema()
    data = load_data()

    if not data:
        pytest.skip("No data rows to validate")

    # Determine column list from schema (supports 'fields' or 'columns')
    schema_fields = schema.get("fields", schema.get("columns", []))
    required_cols = [f.get("name", f) if isinstance(f, dict) else f for f in schema_fields]

    actual_cols = set(data[0].keys())
    missing_cols = set(required_cols) - actual_cols

    assert not missing_cols, f"Missing required columns: {missing_cols}"


def test_column_types():
    """Verify data types match schema definitions."""
    schema = load_schema()
    data = load_data()

    if not data:
        pytest.skip("No data rows to validate")

    schema_fields = {
        f.get("name", f): f for f in schema.get("fields", schema.get("columns", []))
    }

    for row in data:
        for col_name, col_def in schema_fields.items():
            if col_name not in row:
                continue  # Handled by required_columns test

            expected_type = col_def.get("type", "string")
            value = row[col_name]

            if expected_type == "integer":
                try:
                    int(value)
                except ValueError:
                    pytest.fail(f"Expected integer for {col_name}, got: {value}")
            elif expected_type == "float":
                try:
                    float(value)
                except ValueError:
                    pytest.fail(f"Expected float for {col_name}, got: {value}")
            elif expected_type == "boolean":
                if value.lower() not in ("true", "false", "1", "0"):
                    pytest.fail(f"Expected boolean for {col_name}, got: {value}")


def test_not_null_constraints():
    """Verify columns marked as not_null do not contain empty values."""
    schema = load_schema()
    data = load_data()

    if not data:
        pytest.skip("No data rows to validate")

    schema_fields = schema.get("fields", schema.get("columns", []))
    not_null_cols = [
        f.get("name", f) if isinstance(f, dict) else f
        for f in schema_fields
        if (isinstance(f, dict) and f.get("not_null", False))
    ]

    for row in data:
        for col in not_null_cols:
            value = row.get(col)
            if value is None or value.strip() == "":
                pytest.fail(f"Column '{col}' violates not_null constraint with value: {value}")


def test_min_row_count():
    """Verify dataset meets minimum row count (N >= 100)."""
    data = load_data()
    assert len(data) >= 100, f"Dataset has {len(data)} rows, expected >= 100"
