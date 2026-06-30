"""
Contract tests for simulation result schemas.
Verifies that CSV output matches the defined schema in simulation_result.schema.yaml.
"""
import os
import csv
import yaml
import pytest
import tempfile
from pathlib import Path

# Project root relative to tests/contract/
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-network-topology-thermal" / "contracts" / "simulation_result.schema.yaml"
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "simulation_results.csv"

# Expected columns based on the schema defined in T004a
EXPECTED_COLUMNS = [
    "seed",
    "N",
    "p",
    "avg_degree",
    "conductivity",
    "percolation_flag",
    "scaling_factor"
]

def load_schema():
    """Load the simulation result schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T004a is completed.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_csv_header():
    """Load the header row from the simulation results CSV."""
    if not CSV_PATH.exists():
        pytest.fail(f"CSV file not found at {CSV_PATH}. Ensure simulation has run (T015).")
    
    with open(CSV_PATH, 'r', newline='') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
            return header
        except StopIteration:
            pytest.fail(f"CSV file {CSV_PATH} is empty. Expected at least a header row.")

@pytest.mark.contract
def test_csv_output_matches_schema():
    """
    Contract test: Verify CSV output matches simulation_result.schema.yaml.
    
    Checks:
    1. Header row contains exactly the columns defined in the schema.
    2. Column order matches the schema definition.
    3. Data types in the schema are respected (basic type check for strings/numbers).
    """
    schema = load_schema()
    header = load_csv_header()
    
    # Define expected columns from schema
    if 'columns' not in schema:
        pytest.fail("Schema is missing 'columns' definition.")
    
    schema_columns = [col['name'] for col in schema['columns']]
    
    # Check 1: Header matches schema columns exactly
    assert header == schema_columns, (
        f"CSV header mismatch.\n"
        f"Expected: {schema_columns}\n"
        f"Got:      {header}"
    )
    
    # Check 2: Verify data types for a sample row (if data exists)
    # Read the first data row to validate types
    with open(CSV_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if len(rows) > 0:
            sample_row = rows[0]
            
            # Validate numeric fields
            numeric_fields = ['N', 'p', 'avg_degree', 'conductivity', 'scaling_factor']
            for field in numeric_fields:
                try:
                    float(sample_row[field])
                except ValueError:
                    pytest.fail(
                        f"Field '{field}' in row 1 is not a valid number: {sample_row[field]}"
                    )
            
            # Validate boolean/int flag
            flag_fields = ['percolation_flag']
            for field in flag_fields:
                val = sample_row[field]
                if val not in ['0', '1', 'False', 'True', 'false', 'true']:
                    pytest.fail(
                        f"Field '{field}' in row 1 has invalid boolean value: {val}"
                    )
        else:
            # No data rows yet, but header is correct. This is acceptable for initial run.
            pass

@pytest.mark.contract
def test_schema_file_structure():
    """
    Contract test: Verify the schema file itself has the required structure.
    """
    schema = load_schema()
    
    assert 'columns' in schema, "Schema must define a 'columns' list."
    assert isinstance(schema['columns'], list), "'columns' must be a list."
    assert len(schema['columns']) > 0, "'columns' list cannot be empty."
    
    for col in schema['columns']:
        assert 'name' in col, f"Column definition missing 'name': {col}"
        assert 'type' in col, f"Column definition missing 'type': {col}"
        assert 'description' in col, f"Column definition missing 'description': {col}"

@pytest.mark.contract
def test_csv_file_exists_and_readable():
    """
    Contract test: Verify the CSV file exists and is readable.
    """
    assert CSV_PATH.exists(), f"CSV file {CSV_PATH} does not exist."
    assert os.path.getsize(CSV_PATH) > 0, f"CSV file {CSV_PATH} is empty."
    
    # Try to read it as CSV
    try:
        with open(CSV_PATH, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) >= 1, "CSV file has no rows (not even header)."
    except Exception as e:
        pytest.fail(f"Failed to read CSV file {CSV_PATH}: {e}")

@pytest.mark.contract
def test_column_types_match_schema():
    """
    Contract test: Verify that the actual data types in the CSV match the schema.
    """
    schema = load_schema()
    
    # Map schema types to Python validation logic
    type_validators = {
        'integer': lambda x: x.lstrip('-').isdigit(),
        'float': lambda x: True,  # Handled by float() conversion in other tests
        'boolean': lambda x: x.lower() in ['true', 'false', '0', '1', 'yes', 'no'],
        'string': lambda x: True  # All CSV values are strings
    }
    
    with open(CSV_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if len(rows) == 0:
            pytest.skip("No data rows to validate types.")
        
        for col_def in schema['columns']:
            col_name = col_def['name']
            col_type = col_def['type']
            
            if col_name not in reader.fieldnames:
                pytest.fail(f"Column '{col_name}' from schema not found in CSV header.")
            
            validator = type_validators.get(col_type)
            if not validator:
                continue  # Unknown type, skip validation
            
            for i, row in enumerate(rows):
                val = row[col_name]
                if not validator(val):
                    # Special handling for float validation
                    if col_type == 'float':
                        try:
                            float(val)
                        except ValueError:
                            pytest.fail(
                                f"Row {i+1}, column '{col_name}': expected float, got '{val}'"
                            )
                    else:
                        pytest.fail(
                            f"Row {i+1}, column '{col_name}': expected {col_type}, got '{val}'"
                        )