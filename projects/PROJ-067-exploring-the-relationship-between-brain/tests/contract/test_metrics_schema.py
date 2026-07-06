"""
Contract test for metrics CSV schema (Task T022).

This test validates that the output file `data/metrics/subject_metrics.csv`
adheres to the strict schema defined in the project specification.
It ensures that the file exists, has the correct headers, and that data types
are consistent with the expected metrics (Flexibility, Stability) for the
required networks (DMN, Salience, Hippocampal-Memory).
"""
import os
import csv
import pytest
from pathlib import Path

# Expected schema definition
EXPECTED_COLUMNS = [
    "subject_id",
    "network_name",
    "flexibility",
    "stability",
    "n_windows",
    "mean_fd"
]

REQUIRED_NETWORKS = [
    "DMN",
    "Salience",
    "Hippocampal-Memory"
]

METRICS_FILE_PATH = Path("data/metrics/subject_metrics.csv")


def test_metrics_file_exists():
    """Contract: The metrics CSV file must exist after pipeline execution."""
    assert METRICS_FILE_PATH.exists(), (
        f"Contract violation: Metrics file not found at {METRICS_FILE_PATH}. "
        "Ensure US2 (Metric Extraction) has completed successfully."
    )


def test_metrics_file_has_correct_headers():
    """Contract: The CSV must have the exact headers defined in the schema."""
    with open(METRICS_FILE_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)

    # Normalize headers to handle potential whitespace
    header = [h.strip() for h in header]

    assert header == EXPECTED_COLUMNS, (
        f"Contract violation: Header mismatch.\n"
        f"Expected: {EXPECTED_COLUMNS}\n"
        f"Found:    {header}"
    )


def test_metrics_contains_required_networks():
    """Contract: The file must contain rows for DMN, Salience, and Hippocampal-Memory."""
    networks_found = set()

    with open(METRICS_FILE_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            networks_found.add(row['network_name'].strip())

    missing_networks = set(REQUIRED_NETWORKS) - networks_found
    assert not missing_networks, (
        f"Contract violation: Missing required network metrics.\n"
        f"Required: {REQUIRED_NETWORKS}\n"
        f"Found:    {list(networks_found)}\n"
        f"Missing:  {list(missing_networks)}"
    )


def test_metrics_data_types_and_ranges():
    """Contract: Numeric fields must be valid floats within physical bounds."""
    errors = []

    with open(METRICS_FILE_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            # Check subject_id is not empty
            if not row['subject_id'].strip():
                errors.append(f"Row {i}: Empty subject_id")

            # Check numeric fields
            for field in ['flexibility', 'stability', 'n_windows', 'mean_fd']:
                try:
                    val = float(row[field])
                    if field == 'n_windows':
                        if val < 0:
                            errors.append(f"Row {i}: {field} cannot be negative ({val})")
                    elif field in ['flexibility', 'stability', 'mean_fd']:
                        if val < 0:
                            errors.append(f"Row {i}: {field} cannot be negative ({val})")
                except ValueError:
                    errors.append(f"Row {i}: {field} is not a valid float ('{row[field]}')")

    assert not errors, (
        f"Contract violation: Data type or range errors found:\n" + "\n".join(errors)
    )


def test_metrics_not_empty():
    """Contract: The file must contain at least one data row."""
    with open(METRICS_FILE_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        row_count = sum(1 for _ in reader)

    assert row_count > 0, "Contract violation: Metrics file is empty (no data rows)."