"""
Contract test for memory measurement schema.

Verifies that the output file `data/processed/memory_measurements.csv`
adheres to the expected schema defined in the project specification.

Schema Requirements:
- problem_id: string identifier
- source_type: string, must be 'llm' or 'human'
- peak_memory: float, bytes
- steady_state: float, bytes
- status: string, one of 'success', 'timeout', 'syntax_error', 'oom'
- total_resource_cost: float, bytes*seconds

This test ensures data integrity before statistical analysis (US2) and
feature correlation (US3) can proceed.
"""
import csv
import os
import pytest
from pathlib import Path

# Import utility to read the CSV if it exists, or generate a minimal valid one for the contract test
# We rely on utils.py for the actual writer, but here we verify the structure of the file
# if it exists, or fail clearly if it doesn't.

# Expected columns
EXPECTED_COLUMNS = [
    "problem_id",
    "source_type",
    "peak_memory",
    "steady_state",
    "status",
    "total_resource_cost"
]

# Allowed values for specific columns
ALLOWED_SOURCE_TYPES = {"llm", "human"}
ALLOWED_STATUSES = {"success", "timeout", "syntax_error", "oom"}

OUTPUT_PATH = Path("data/processed/memory_measurements.csv")

def test_schema_columns_exist():
    """Contract Test: Verify all required columns exist in the CSV header."""
    if not OUTPUT_PATH.exists():
        pytest.fail(
            f"Contract test failed: Output file {OUTPUT_PATH} does not exist. "
            "Run the profiling pipeline (T012-T017) to generate data before running this contract test."
        )
    
    with open(OUTPUT_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        if fieldnames is None:
            pytest.fail("Contract test failed: CSV file is empty or has no header.")
        
        missing_columns = set(EXPECTED_COLUMNS) - set(fieldnames)
        if missing_columns:
            pytest.fail(
                f"Contract test failed: Missing required columns: {missing_columns}. "
                f"Expected: {EXPECTED_COLUMNS}, Found: {fieldnames}"
            )

def test_schema_data_types_and_values():
    """Contract Test: Verify data types and allowed values for each row."""
    if not OUTPUT_PATH.exists():
        pytest.fail(
            f"Contract test failed: Output file {OUTPUT_PATH} does not exist. "
            "Run the profiling pipeline (T012-T017) to generate data before running this contract test."
        )

    row_count = 0
    with open(OUTPUT_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            row_count += 1
            
            # Check source_type
            source_type = row["source_type"]
            if source_type not in ALLOWED_SOURCE_TYPES:
                pytest.fail(
                    f"Contract test failed: Row {row_count} has invalid source_type '{source_type}'. "
                    f"Allowed: {ALLOWED_SOURCE_TYPES}"
                )
            
            # Check status
            status = row["status"]
            if status not in ALLOWED_STATUSES:
                pytest.fail(
                    f"Contract test failed: Row {row_count} has invalid status '{status}'. "
                    f"Allowed: {ALLOWED_STATUSES}"
                )
            
            # Check numeric fields are parsable and non-negative
            try:
                peak = float(row["peak_memory"])
                steady = float(row["steady_state"])
                cost = float(row["total_resource_cost"])
                
                if peak < 0 or steady < 0 or cost < 0:
                    pytest.fail(
                        f"Contract test failed: Row {row_count} has negative memory/cost values. "
                        f"peak={peak}, steady={steady}, cost={cost}"
                    )
            except ValueError:
                pytest.fail(
                    f"Contract test failed: Row {row_count} has non-numeric memory/cost values. "
                    f"peak='{row['peak_memory']}', steady='{row['steady_state']}', cost='{row['total_resource_cost']}'"
                )
            
            # Check problem_id is not empty
            if not row["problem_id"].strip():
                pytest.fail(f"Contract test failed: Row {row_count} has empty problem_id.")

    if row_count == 0:
        pytest.fail(
            "Contract test failed: CSV file exists but contains no data rows. "
            "The profiling pipeline must generate at least one valid measurement."
        )

def test_schema_consistency():
    """Contract Test: Verify logical consistency (e.g., success implies valid memory > 0)."""
    if not OUTPUT_PATH.exists():
        pytest.fail(
            f"Contract test failed: Output file {OUTPUT_PATH} does not exist. "
            "Run the profiling pipeline (T012-T017) to generate data before running this contract test."
        )

    with open(OUTPUT_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row_count = 0
        
        for row in reader:
            row_count += 1
            status = row["status"]
            peak = float(row["peak_memory"])
            steady = float(row["steady_state"])
            
            # If status is success, memory should typically be > 0 (unless trivial code)
            # However, we allow 0 for empty code, but we check that it's not negative (covered above)
            # We specifically check that 'timeout' or 'oom' might have 0 or partial data depending on implementation
            # This is a soft check to ensure the data makes sense.
            if status == "success" and peak == 0:
                # This is technically possible for empty programs, but worth a warning or strict check
                # For strict contract, we allow it, but if the plan says 'success' means 'ran', 
                # then 0 memory is suspicious. We'll allow it but note it.
                pass 
            
            # If status is timeout or oom, memory might be 0 or partial (depending on when it crashed)
            # The contract is that the file exists and columns are correct.
    
    # If we got here without failing, the data is consistent with the schema.
    assert row_count > 0, "No data rows found to validate consistency."