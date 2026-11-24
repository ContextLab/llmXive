"""
Test suite to validate the reference data file produced by T002.

This test validates `tests/data/reference_values.csv` to ensure:
1. The file exists and is readable.
2. It contains the required columns: 'n' and 'p_P_n'.
3. All values in 'n' are positive integers within [1, 100].
4. All values in 'p_P_n' are non‑negative integers.
5. The first 20 rows match the known reference values for distinct‑prime partitions.
"""
import os
import csv
import pytest

# Path to the reference data file
REFERENCE_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "reference_values.csv"
)

REQUIRED_COLUMNS = ['n', 'p_P_n']
MIN_N = 1
MAX_N = 100

# Known reference values for n = 1 .. 20 (distinct‑prime partitions)
EXPECTED_FIRST_20 = [
    (1, 0), (2, 1), (3, 1), (4, 0), (5, 2),
    (6, 0), (7, 2), (8, 1), (9, 1), (10, 2),
    (11, 1), (12, 2), (13, 2), (14, 2), (15, 2),
    (16, 3), (17, 2), (18, 4), (19, 3), (20, 4)
]

def test_reference_file_exists():
    """Verify that the reference data file exists."""
    assert os.path.isfile(REFERENCE_FILE_PATH), (
        f"Reference file not found at {REFERENCE_FILE_PATH}. "
        "Ensure T002 (generate_reference.py) has been executed."
    )

def test_reference_file_has_correct_headers():
    """Verify that the CSV file contains the required column headers."""
    with open(REFERENCE_FILE_PATH, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)

    # Normalize headers (strip whitespace)
    headers = [h.strip() for h in headers]

    for col in REQUIRED_COLUMNS:
        assert col in headers, (
            f"Missing required column '{col}' in {REFERENCE_FILE_PATH}. "
            f"Found headers: {headers}"
        )

def test_reference_data_types_and_ranges():
    """
    Verify that all data rows contain valid integers and correct ranges.
    Checks:
    - 'n' is in range [1, 100].
    - 'p_P_n' is a non‑negative integer.
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

            assert MIN_N <= n_val <= MAX_N, (
                f"Value of n={n_val} is outside expected range [{MIN_N}, {MAX_N}]"
            )
            assert n_val not in seen_n, f"Duplicate value for n={n_val} found in reference data"
            seen_n.add(n_val)

            # Validate 'p_P_n'
            try:
                count_val = int(row['p_P_n'].strip())
            except ValueError:
                raise AssertionError(f"Value for 'p_P_n' is not an integer: {row['p_P_n']}")

            assert count_val >= 0, (
                f"Partition count p_P_n={count_val} for n={n_val} is negative"
            )

        # Verify we have exactly 100 rows (n=1 to n=100)
        expected_rows = MAX_N - MIN_N + 1
        assert row_count == expected_rows, (
            f"Expected {expected_rows} rows in reference data, found {row_count}"
        )

def test_first_20_rows_match_reference():
    """Assert that the first 20 rows match the known reference values."""
    with open(REFERENCE_FILE_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for idx, expected in enumerate(EXPECTED_FIRST_20):
            try:
                row = next(reader)
            except StopIteration:
                raise AssertionError(
                    f"Reference file ended early; expected at least 20 rows, got {idx}"
                )
            n_val = int(row['n'].strip())
            p_val = int(row['p_P_n'].strip())
            assert (n_val, p_val) == expected, (
                f"Row {idx + 1} mismatch: expected (n={expected[0]}, p_P_n={expected[1]}), "
                f"got (n={n_val}, p_P_n={p_val})"
            )