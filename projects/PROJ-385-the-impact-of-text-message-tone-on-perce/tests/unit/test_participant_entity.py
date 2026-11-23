"""
Test for T086: Validate Participant entity.

Ensures data/processed/anonymised_ratings.csv contains a non-null
participant_id column matching the Participant schema.

Verification: Test fails if column missing or malformed.
"""
import csv
import re
import pytest
from pathlib import Path
import sys
import os

# Add project root to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_processed_data_dir
from logging_config import setup_logging

# Configure logging to avoid errors if not set up by pipeline
try:
    setup_logging()
except Exception:
    pass

ANONYMISED_RATINGS_PATH = Path(get_processed_data_dir()) / "anonymised_ratings.csv"

# Pattern for a hashed participant ID (SHA-256 produces 64 hex chars)
# The schema expects a non-null string identifier.
PARTICIPANT_ID_PATTERN = re.compile(r'^[0-9a-f]{64}$')

def test_participant_id_column_exists():
    """Verify that the participant_id column exists in the CSV."""
    if not ANONYMISED_RATINGS_PATH.exists():
        pytest.fail(f"File not found: {ANONYMISED_RATINGS_PATH}. "
                    "Ensure T051 (Anonymise ratings) has been run.")
    
    with open(ANONYMISED_RATINGS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if headers is None:
            pytest.fail("CSV file is empty or has no headers.")
        
        assert 'participant_id' in headers, (
            f"Column 'participant_id' missing from headers. "
            f"Found: {headers}"
        )

def test_participant_id_non_null_and_valid_format():
    """Verify that every participant_id is non-null and matches the expected format."""
    if not ANONYMISED_RATINGS_PATH.exists():
        pytest.fail(f"File not found: {ANONYMISED_RATINGS_PATH}. "
                    "Ensure T051 (Anonymise ratings) has been run.")
    
    row_count = 0
    valid_count = 0
    invalid_rows = []

    with open(ANONYMISED_RATINGS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_idx, row in enumerate(reader, start=2): # Start at 2 for 1-based row count (header is 1)
            row_count += 1
            pid = row.get('participant_id')

            # Check for null/empty
            if pid is None or pid.strip() == '':
                invalid_rows.append((row_idx, "Empty or null participant_id"))
                continue

            # Check format (SHA-256 hash is 64 hex characters)
            if not PARTICIPANT_ID_PATTERN.match(pid):
                invalid_rows.append((row_idx, f"Invalid format: '{pid}'"))
                continue

            valid_count += 1

    if row_count == 0:
        pytest.fail("CSV file contains no data rows.")

    if invalid_rows:
        error_details = "\n".join([f"Row {r}: {e}" for r, e in invalid_rows[:5]])
        pytest.fail(
            f"Found {len(invalid_rows)} rows with invalid or missing participant_id. "
            f"First 5 errors:\n{error_details}"
        )

    assert valid_count == row_count, (
        f"All {row_count} rows must have a valid, non-null participant_id. "
        f"Found {valid_count} valid rows."
    )
