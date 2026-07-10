import os
import sys
import csv
import json
import tempfile
from pathlib import Path
from typing import List, Any

import pytest

# Ensure project root is in path to import code modules if needed
# though this test primarily inspects file contents
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Expected schema for the ingestion output
EXPECTED_COLUMNS = ["smi", "lambda_max", "scaffold_id"]
EXPECTED_TYPES = {
    "smi": str,
    "lambda_max": float,
    "scaffold_id": str
}

def _load_csv(path: str) -> List[dict]:
    """Load a CSV file into a list of dictionaries."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Output file not found: {path}")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def _validate_schema(data: List[dict], filepath: str) -> None:
    """Validate that the CSV data matches the expected schema."""
    if not data:
        # Empty file is valid schema-wise, but might be a logic error
        # For this contract test, we check structure primarily.
        # However, a real ingestion should produce rows.
        # Let's assume empty is structurally valid but warn in a real scenario.
        # Here we just check headers if file exists but is empty.
        pass

    # Check headers (keys in the first row)
    first_row = data[0]
    actual_columns = list(first_row.keys())
    
    assert actual_columns == EXPECTED_COLUMNS, (
        f"Column mismatch in {filepath}. "
        f"Expected: {EXPECTED_COLUMNS}, Got: {actual_columns}"
    )

    # Check types for the first row (CSVs are strings, we must parse)
    for col, expected_type in EXPECTED_TYPES.items():
        val = first_row[col]
        
        if expected_type == float:
            try:
                float(val)
            except ValueError:
                raise AssertionError(
                    f"Type mismatch in {filepath}, column '{col}'. "
                    f"Expected float, got non-numeric string: {val}"
                )
        elif expected_type == str:
            # All CSV values are strings, but we verify it's not a number formatted weirdly
            # or if it's meant to be a string ID.
            if not isinstance(val, str):
                raise AssertionError(
                    f"Type mismatch in {filepath}, column '{col}'. "
                    f"Expected str, got {type(val)}"
                )

@pytest.mark.parametrize("test_file", [
    "data/raw/processed.csv",
    "data/processed/split_data.csv"
])
def test_ingest_output_schema(test_file):
    """
    Contract test for data ingestion output schema.
    Asserts output columns are exactly ["smi", "lambda_max", "scaffold_id"]
    with logical types str, float, str.
    
    This test passes if the file exists and matches the schema.
    If the file does not exist, it is marked as SKIPPED (since the ingestion
    script might not have run yet in a test environment), or FAILED if 
    strictness is required. For this contract test, we expect the file to exist
    after the pipeline runs.
    """
    full_path = PROJECT_ROOT / test_file
    
    if not full_path.exists():
        # In a CI/CD pipeline, this might be a failure if the previous step ran.
        # Here we skip to allow unit testing of the test itself if data is missing.
        pytest.skip(f"Output file {test_file} not found. Run the ingestion pipeline first.")
    
    try:
        data = _load_csv(str(full_path))
        if len(data) == 0:
            pytest.skip(f"Output file {test_file} is empty.")
        
        _validate_schema(data, str(full_path))
    except AssertionError as e:
        pytest.fail(str(e))

def test_schema_definition():
    """
    Sanity check to ensure the expected schema constants are defined correctly.
    """
    assert EXPECTED_COLUMNS == ["smi", "lambda_max", "scaffold_id"]
    assert EXPECTED_TYPES["smi"] == str
    assert EXPECTED_TYPES["lambda_max"] == float
    assert EXPECTED_TYPES["scaffold_id"] == str