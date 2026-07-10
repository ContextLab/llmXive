"""
Contract test for data ingestion output schema (US1).

This test verifies that the data ingestion pipeline produces an output
that strictly adheres to the schema defined in:
specs/001-predict-voc-profiles/contracts/dataset.schema.yaml

It validates:
1. File existence and format (CSV).
2. Required columns presence.
3. Data types for critical columns (numeric vs categorical).
4. Absence of non-numeric entries in numeric fields.
5. Minimum row count (>= 50) as per the MVP checkpoint.
"""
import os
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from typing import Dict, Any, List, Set

# Import project utilities if needed, though this is a pure contract test
# We assume the ingestion script (T014) runs before this test in the CI/CD flow
# or we run the generator (T005) to ensure data exists.

# Constants based on project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-predict-voc-profiles" / "contracts" / "dataset.schema.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "merged_dataset.csv"
SYNTHETIC_SOURCE = PROJECT_ROOT / "data" / "raw" / "synthetic_arabidopsis_v1.csv"

def load_schema() -> Dict[str, Any]:
    """Load the dataset schema definition."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def ensure_data_exists():
    """
    Ensure the output file exists. If not, attempt to generate synthetic data
    via T005 to satisfy the test environment.
    """
    if OUTPUT_PATH.exists():
        return

    if SYNTHETIC_SOURCE.exists():
        # If raw synthetic exists but processed doesn't, we might need to run the pipeline.
        # For this contract test, we assume the pipeline (T014/T015) has run.
        # If the output is missing, we fail the test rather than silently generating it,
        # because the test is verifying the *output* of the ingestion task.
        # However, to make the test runnable in isolation for T010 implementation,
        # we will trigger the synthetic generator if the raw file is missing.
        pass
    
    # If the processed file is missing, the test fails. 
    # In a real CI, T014 runs before T010.
    # For the purpose of this task implementation, we assume the file should be there.
    # If it's not, we raise a clear assertion error.
    if not OUTPUT_PATH.exists():
        # Attempt to run the generator if raw is missing, just in case
        if not SYNTHETIC_SOURCE.exists():
            try:
                from generators.synthetic_data import main
                main()
            except Exception:
                pass # Ignore, test will fail below

def test_ingest_schema_contract():
    """
    Contract Test: Verify the merged dataset matches the schema.
    """
    # 1. Ensure data is present (simulate pipeline run if needed for local dev)
    # In a strict CI, this would be a setup fixture. Here we check existence.
    if not OUTPUT_PATH.exists():
        # If the file doesn't exist, the ingestion task (T014/15) hasn't run.
        # We cannot validate the schema.
        pytest.fail(f"Output file {OUTPUT_PATH} does not exist. Ingestion pipeline not run.")

    # 2. Load Schema
    schema = load_schema()
    expected_columns = schema.get("required_columns", [])
    column_types = schema.get("column_types", {})
    min_rows = schema.get("min_rows", 50)

    # 3. Load Data
    try:
        df = pd.read_csv(OUTPUT_PATH)
    except Exception as e:
        pytest.fail(f"Failed to read CSV: {e}")

    # 4. Check Row Count
    assert len(df) >= min_rows, (
        f"Dataset has {len(df)} rows, but schema requires >= {min_rows} rows."
    )

    # 5. Check Required Columns
    missing_cols = set(expected_columns) - set(df.columns)
    assert not missing_cols, (
        f"Missing required columns: {missing_cols}. "
        f"Expected: {expected_columns}, Found: {list(df.columns)}"
    )

    # 6. Validate Data Types and Content
    numeric_columns = [col for col, dtype in column_types.items() if dtype == "numeric"]
    categorical_columns = [col for col, dtype in column_types.items() if dtype == "categorical"]
    
    errors = []

    for col in numeric_columns:
        if col in df.columns:
            # Check for non-numeric values (including NaN if not allowed, but usually allowed)
            # We check if the series can be coerced to numeric without errors (excluding NaN)
            # Actually, pandas read_csv might read numbers as objects if mixed.
            # We enforce that they MUST be numeric types or coercible.
            try:
                # Attempt conversion to float, ignoring NaN
                pd.to_numeric(df[col], errors='raise')
            except ValueError as e:
                errors.append(f"Column '{col}' contains non-numeric values: {e}")

    for col in categorical_columns:
        if col in df.columns:
            # Ensure it's not purely numeric if expected to be categorical (optional check)
            # Main check is that it exists.
            if df[col].dtype == 'float64' or df[col].dtype == 'int64':
                # It's okay if it's numeric, but let's verify it's not empty
                if df[col].empty:
                    errors.append(f"Column '{col}' is empty.")

    if errors:
        pytest.fail("Schema validation errors:\n" + "\n".join(errors))

    # 7. Check for Critical Nulls (if defined in schema)
    # Assuming schema might have "critical_fields" that cannot be null
    critical_fields = schema.get("critical_fields", [])
    for field in critical_fields:
        if field in df.columns:
            null_count = df[field].isnull().sum()
            if null_count > 0:
                errors.append(f"Critical field '{field}' has {null_count} null values.")
    
    if errors:
        pytest.fail("Critical field validation errors:\n" + "\n".join(errors))

def test_data_integrity_replicates():
    """
    Integration-style check: Verify replicate logic is consistent with T006.
    This ensures the ingestion pipeline respected the replicate exclusion logic.
    """
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file not found.")

    df = pd.read_csv(OUTPUT_PATH)
    schema = load_schema()
    
    # Assuming 'condition_id' or similar is the grouping key for replicates
    # The schema should define the grouping key.
    group_key = schema.get("grouping_key", "condition_id")
    
    if group_key not in df.columns:
        # If the key isn't there, we can't test this specific contract
        pytest.skip(f"Grouping key '{group_key}' not found in schema.")

    # Check that no group has < 3 replicates (FR-011 logic)
    # Note: If the ingestion pipeline (T015) did its job, this should hold.
    # If it fails, the ingestion logic is flawed.
    counts = df.groupby(group_key).size()
    low_replicate_groups = counts[counts < 3]
    
    assert len(low_replicate_groups) == 0, (
        f"Found {len(low_replicate_groups)} condition groups with < 3 replicates. "
        f"Violates FR-011. Groups: {low_replicate_groups.index.tolist()}"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
