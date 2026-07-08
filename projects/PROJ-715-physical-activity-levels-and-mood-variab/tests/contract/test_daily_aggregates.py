"""
Contract tests for daily_aggregates.csv schema.

Validates that the output file from User Story 1 (T016) adheres to the
schema defined in specs/001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml.
"""
import os
import csv
import json
import pytest
from pathlib import Path

import yaml

# Import path utility from project config
from config import get_path


def load_schema():
    """Load the daily_aggregates schema definition."""
    schema_path = get_path("specs/001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_data():
    """Load the daily_aggregates.csv file."""
    data_path = get_path("data/processed/daily_aggregates.csv")
    if not os.path.exists(data_path):
        pytest.fail(f"Data file not found at {data_path}. Has T016 been run?")
    return data_path


def test_schema_file_exists():
    """Verify that the schema definition file exists."""
    schema_path = get_path("specs/001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml")
    assert os.path.exists(schema_path), f"Schema file missing: {schema_path}"


def test_data_file_exists():
    """Verify that the daily_aggregates.csv file exists."""
    data_path = get_path("data/processed/daily_aggregates.csv")
    assert os.path.exists(data_path), f"Data file missing: {data_path}"


def test_required_columns_present():
    """Check that all required columns defined in schema are present."""
    schema = load_schema()
    required_columns = schema.get("required_columns", [])
    
    data_path = load_data()
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
    assert headers is not None, "CSV file is empty or has no headers"
    
    missing = set(required_columns) - set(headers)
    assert not missing, f"Missing required columns: {missing}"


def test_column_types_and_constraints():
    """Validate data types and constraints for each column."""
    schema = load_schema()
    columns_schema = schema.get("columns", {})
    
    data_path = load_data()
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) > 0, "CSV file contains no data rows"
    
    for row_num, row in enumerate(rows, start=1):
        for col_name, constraints in columns_schema.items():
            if col_name not in row:
                continue  # Handled by required_columns test
            
            value = row[col_name]
            
            # Check non-null constraint
            if constraints.get("nullable") is False:
                assert value != "" and value is not None, \
                    f"Row {row_num}, Column '{col_name}': Value cannot be null"
            
            # Check numeric constraints
            if constraints.get("type") == "numeric":
                try:
                    float_val = float(value)
                    if "min" in constraints:
                        assert float_val >= constraints["min"], \
                            f"Row {row_num}, Column '{col_name}': {float_val} < {constraints['min']}"
                    if "max" in constraints:
                        assert float_val <= constraints["max"], \
                            f"Row {row_num}, Column '{col_name}': {float_val} > {constraints['max']}"
                except ValueError:
                    raise AssertionError(
                        f"Row {row_num}, Column '{col_name}': Value '{value}' is not a valid number"
                    )
            
            # Check string constraints (e.g., categorical values)
            if constraints.get("type") == "categorical":
                allowed = constraints.get("values", [])
                if allowed:
                    assert value in allowed, \
                        f"Row {row_num}, Column '{col_name}': '{value}' not in {allowed}"


def test_row_count_matches_valid_participant_days():
    """Verify that the row count is reasonable (non-zero)."""
    data_path = load_data()
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # At least one row should exist if data was processed
    assert len(rows) > 0, "No rows found in daily_aggregates.csv. Data processing may have failed."
    
    # Optional: Check against expected participant count if available in config
    # For now, just ensure it's not empty
    assert len(rows) >= 1, "Expected at least one participant-day record"


def test_unique_participant_day_combinations():
    """Ensure no duplicate participant-day entries."""
    data_path = load_data()
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    seen = set()
    for row in rows:
        # Assuming 'participant_id' and 'date' form the unique key
        if "participant_id" in row and "date" in row:
            key = (row["participant_id"], row["date"])
            assert key not in seen, f"Duplicate entry found: {key}"
            seen.add(key)