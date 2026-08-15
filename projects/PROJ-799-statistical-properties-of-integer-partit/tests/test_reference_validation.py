"""
Test suite to validate the reference data file produced by T008.

This task validates `tests/data/reference_values.csv` to ensure:
1. The file exists and is readable.
2. It contains the required columns: 'n' and 'p_P(n)'.
3. All values in 'n' are positive integers.
4. All values in 'p_P(n)' are non-negative integers.
5. The data range covers n in [1, 100].

This is a contract test for the reference data generation (T008).
"""
import os
import csv
import pytest
import numpy as np

# Path to the reference data file
REFERENCE_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "tests",
    "data",
    "reference_values.csv"
)

REQUIRED_COLUMNS = ['n', 'p_P(n)']
MIN_N = 1
MAX_N = 100

def test_reference_file_exists():
    """Verify that the reference data file exists."""
    assert os.path.isfile(REFERENCE_FILE_PATH), \
        f"Reference file not found at {REFERENCE_FILE_PATH}. " \
        "Ensure T008 (generate_reference.py) has been executed."

def test_reference_file_has_correct_headers():
    """Verify that the CSV file contains the required column headers."""
    with open(REFERENCE_FILE_PATH, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)
    
    # Normalize headers (strip whitespace)
    headers = [h.strip() for h in headers]
    
    for col in REQUIRED_COLUMNS:
        assert col in headers, \
            f"Missing required column '{col}' in {REFERENCE_FILE_PATH}. " \
            f"Found headers: {headers}"

def test_reference_data_types_and_values():
    """
    Verify that all data rows contain valid integers and correct ranges.
    
    Checks:
    - 'n' is in range [1, 100].
    - 'p_P(n)' is a non-negative integer.
    - No duplicate 'n' values.
    """
    with open(REFERENCE_FILE_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        seen_n = set()
        row_count = 0
        
        for row in reader:
            row_count += 1
            
            # Validate 'n'
            try:
                n_val = int(row['n'].strip())
            except ValueError:
                raise AssertionError(f"Value for 'n' is not an integer: {row['n']}")
            
            assert MIN_N <= n_val <= MAX_N, \
                f"Value of n={n_val} is outside expected range [{MIN_N}, {MAX_N}]"
            
            assert n_val not in seen_n, \
                f"Duplicate value for n={n_val} found in reference data"
            seen_n.add(n_val)
            
            # Validate 'p_P(n)'
            try:
                count_val = int(row['p_P(n)'].strip())
            except ValueError:
                raise AssertionError(f"Value for 'p_P(n)' is not an integer: {row['p_P(n)']}")
            
            assert count_val >= 0, \
                f"Partition count p_P(n)={count_val} for n={n_val} is negative"
    
    # Verify we have exactly 100 rows (n=1 to n=100)
    expected_rows = MAX_N - MIN_N + 1
    assert row_count == expected_rows, \
        f"Expected {expected_rows} rows in reference data, found {row_count}"

def test_reference_data_completeness():
    """
    Verify that the dataset contains entries for every integer from 1 to 100.
    """
    with open(REFERENCE_FILE_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        n_values = set()
        for row in reader:
            n_values.add(int(row['n'].strip()))
    
    expected_n_values = set(range(MIN_N, MAX_N + 1))
    missing_values = expected_n_values - n_values
    
    assert not missing_values, \
        f"Reference data is missing entries for n={sorted(missing_values)}"