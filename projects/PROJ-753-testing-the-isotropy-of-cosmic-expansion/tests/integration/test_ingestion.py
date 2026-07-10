"""
Integration test for User Story 1: Data Ingestion and Residual Calculation.

Verifies:
1. The output CSV `data/processed/residuals.csv` exists and has the expected row count
   (matching the Pantheon+ full sample within redshift cuts).
2. Coordinate validity: RA is within [0, 360) and Dec is within [-90, 90].
3. Data types and basic schema compliance.

This test assumes T012 (Ingestion) and T016 (Writing residuals) have been executed
to produce the target file.
"""
import csv
import os
import math
from pathlib import Path

import pytest

# Import project root helper from conftest
from conftest import project_root


@pytest.fixture
def residuals_path():
    """Path to the expected residuals CSV output."""
    return Path(project_root()) / "data" / "processed" / "residuals.csv"


@pytest.fixture
def expected_row_count():
    """
    Expected number of rows in the residuals CSV.
    
    The Pantheon+ full sample contains 1701 supernovae.
    The task description for T012/T016 implies filtering for missing values,
    but the spec for T011 mentions "within redshift cuts" matching the 'full' sample.
    We assert a minimum threshold of 1000 to account for potential filtering of
    bad data, but expect close to 1701 if the cut is minimal (missing values only).
    If T012/T016 implements a specific redshift cut (e.g., z > 0.01), the count
    will be lower. We use a safe lower bound of 1500 for the 'full' sample logic
    described in the task prompt, assuming standard quality cuts.
    """
    # Pantheon+ has 1701 SNe.
    # We expect at least 1500 to pass basic validity checks.
    return 1500


def test_residuals_file_exists(residuals_path):
    """Verify that the ingestion script produced the output file."""
    assert residuals_path.exists(), f"Residuals file not found at {residuals_path}. " \
                                    "Ensure T012 (ingest) and T016 (write) have run."


def test_residuals_row_count(residuals_path, expected_row_count):
    """
    Verify the row count matches the expected Pantheon+ full sample size.
    
    Note: This test counts data rows (excluding header).
    """
    with open(residuals_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row_count = sum(1 for _ in reader)
    
    assert row_count >= expected_row_count, (
        f"Row count ({row_count}) is below expected minimum ({expected_row_count}). "
        "Check if ingestion logic is too aggressive or if the file is incomplete."
    )
    # Optional: upper bound check if we expect exactly 1701 minus very few exclusions
    assert row_count <= 1705, (
        f"Row count ({row_count}) exceeds known Pantheon+ sample size (1701). "
        "Check for duplicate entries or data corruption."
    )


def test_coordinate_validity(residuals_path):
    """
    Verify that RA and Dec values are within valid celestial coordinate ranges.
    
    RA: [0, 360) degrees
    Dec: [-90, 90] degrees
    """
    with open(residuals_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row_count = 0
        for row in reader:
            row_count += 1
            
            # Validate RA
            try:
                ra = float(row['RA'])
                assert 0.0 <= ra < 360.0, (
                    f"Row {row_count}: RA value {ra} is out of range [0, 360)."
                )
            except (ValueError, KeyError) as e:
                pytest.fail(f"Row {row_count}: Invalid or missing RA data: {e}")
            
            # Validate Dec
            try:
                dec = float(row['Dec'])
                assert -90.0 <= dec <= 90.0, (
                    f"Row {row_count}: Dec value {dec} is out of range [-90, 90]."
                )
            except (ValueError, KeyError) as e:
                pytest.fail(f"Row {row_count}: Invalid or missing Dec data: {e}")
    
    assert row_count > 0, "No data rows found to validate coordinates."


def test_schema_columns(residuals_path):
    """
    Verify the CSV contains all required columns as defined in T016.
    
    Expected columns: ID, RA, Dec, z, mu_obs, sigma_mu, mu_th, residual
    """
    expected_columns = {'ID', 'RA', 'Dec', 'z', 'mu_obs', 'sigma_mu', 'mu_th', 'residual'}
    
    with open(residuals_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        actual_columns = set(reader.fieldnames)
    
    missing = expected_columns - actual_columns
    extra = actual_columns - expected_columns
    
    assert not missing, f"Missing required columns: {missing}"
    # Extra columns are allowed (e.g., metadata), but we log them for awareness
    if extra:
        pytest.skip(f"Note: Extra columns found: {extra}. This is acceptable.")
    
    assert actual_columns == expected_columns, "Column mismatch."