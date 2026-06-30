"""
Contract test for hallucination_rates.csv schema.

This test defines the exact schema requirements for the output file
`results/hallucination_rates.csv` and validates that any generated
output conforms to these requirements before downstream tasks (T012-T018)
can proceed.

Schema Definition:
- File: results/hallucination_rates.csv
- Columns: ['domain', 'rate', 'ci_lower', 'ci_upper']
- Types:
    - domain: str (one of 'speech', 'music', 'env')
    - rate: float (0.0 <= rate <= 1.0)
    - ci_lower: float (0.0 <= ci_lower <= 1.0)
    - ci_upper: float (0.0 <= ci_upper <= 1.0)
- Constraints:
    - ci_lower <= rate <= ci_upper
    - Exactly 3 rows (one per domain)
"""

import csv
import os
import pytest
from pathlib import Path

# Expected schema constants
EXPECTED_COLUMNS = ['domain', 'rate', 'ci_lower', 'ci_upper']
EXPECTED_DOMAINS = {'speech', 'music', 'env'}
REQUIRED_ROW_COUNT = 3

OUTPUT_PATH = Path('results/hallucination_rates.csv')

def _validate_row(row: dict) -> list:
    """
    Validates a single row against the schema.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    
    # Check required columns exist
    for col in EXPECTED_COLUMNS:
        if col not in row:
            errors.append(f"Missing required column: '{col}'")
    
    if errors:
        return errors
    
    domain = row['domain']
    try:
        rate = float(row['rate'])
        ci_lower = float(row['ci_lower'])
        ci_upper = float(row['ci_upper'])
    except ValueError as e:
        errors.append(f"Non-numeric value found: {e}")
        return errors
    
    # Validate domain
    if domain not in EXPECTED_DOMAINS:
        errors.append(f"Invalid domain '{domain}'. Must be one of {EXPECTED_DOMAINS}")
    
    # Validate ranges
    if not (0.0 <= rate <= 1.0):
        errors.append(f"Rate {rate} out of range [0.0, 1.0]")
    if not (0.0 <= ci_lower <= 1.0):
        errors.append(f"CI Lower {ci_lower} out of range [0.0, 1.0]")
    if not (0.0 <= ci_upper <= 1.0):
        errors.append(f"CI Upper {ci_upper} out of range [0.0, 1.0]")
    
    # Validate logical consistency
    if not (ci_lower <= rate <= ci_upper):
        errors.append(f"Logical error: ci_lower ({ci_lower}) <= rate ({rate}) <= ci_upper ({ci_upper})")
    
    return errors

def test_file_exists():
    """Contract: The output file must exist."""
    assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} does not exist. Run T017b first."

def test_file_has_correct_columns():
    """Contract: The file must have exactly the required columns."""
    with open(OUTPUT_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        actual_columns = reader.fieldnames
        
        assert actual_columns is not None, "CSV file is empty or has no header"
        
        missing = set(EXPECTED_COLUMNS) - set(actual_columns)
        extra = set(actual_columns) - set(EXPECTED_COLUMNS)
        
        assert not missing, f"Missing required columns: {missing}"
        assert not extra, f"Unexpected extra columns: {extra}"

def test_file_has_correct_row_count():
    """Contract: The file must have exactly 3 rows (one per domain)."""
    with open(OUTPUT_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == REQUIRED_ROW_COUNT, f"Expected {REQUIRED_ROW_COUNT} rows, found {len(rows)}"

def test_file_has_all_domains():
    """Contract: All required domains must be present."""
    with open(OUTPUT_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        domains = {row['domain'] for row in reader}
        
        missing_domains = EXPECTED_DOMAINS - domains
        assert not missing_domains, f"Missing domains: {missing_domains}"

def test_all_rows_valid():
    """Contract: Every row must pass schema validation."""
    with open(OUTPUT_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        all_errors = []
        for i, row in enumerate(reader):
            errors = _validate_row(row)
            if errors:
                all_errors.append(f"Row {i+1}: {errors}")
        
        assert not all_errors, f"Validation errors found:\n" + "\n".join(all_errors)

def test_schema_contract():
    """
    Master contract test. Runs all schema checks.
    If this fails, T012-T018 must not proceed until fixed.
    """
    # Run all individual checks
    test_file_exists()
    test_file_has_correct_columns()
    test_file_has_correct_row_count()
    test_file_has_all_domains()
    test_all_rows_valid()