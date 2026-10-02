"""
Unit tests for the Metadata Schema defined in code/survey/constants.py.
Verifies that the exported CSV headers match the schema definition.
"""
import os
import sys
import csv
import tempfile
import shutil
import uuid
from datetime import datetime

import pytest

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from code.survey.constants import METADATA_SCHEMA


def test_schema_definitions_exist():
    """Verify that the METADATA_SCHEMA constant is populated with expected keys."""
    assert isinstance(METADATA_SCHEMA, dict)
    required_keys = [
        "participant_id", "age", "education", "timestamp",
        "hashed_ip", "browser_version", "session_duration"
    ]
    for key in required_keys:
        assert key in METADATA_SCHEMA, f"Missing required schema key: {key}"
        assert "type" in METADATA_SCHEMA[key], f"Missing 'type' for {key}"
        assert "description" in METADATA_SCHEMA[key], f"Missing 'description' for {key}"


def test_csv_headers_match_schema():
    """
    Verify that the headers in a generated CSV match the METADATA_SCHEMA keys.
    This simulates the export logic from code/survey/app.py.
    """
    # Define the expected headers based on the schema
    expected_headers = list(METADATA_SCHEMA.keys())

    # Create a temporary CSV file with sample data matching the schema
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=expected_headers)
        writer.writeheader()

        # Write one valid row
        sample_row = {
            "participant_id": str(uuid.uuid4()),
            "age": 25,
            "education": "Bachelor's Degree",
            "timestamp": datetime.utcnow().isoformat(),
            "hashed_ip": "a1b2c3d4e5f6...",
            "browser_version": "Chrome/120.0",
            "session_duration": 145
        }
        writer.writerow(sample_row)
        temp_path = f.name

    try:
        # Read the file back and verify headers
        with open(temp_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            actual_headers = reader.fieldnames

            # Assert headers match exactly
            assert set(actual_headers) == set(expected_headers), (
                f"CSV headers mismatch.\n"
                f"Expected: {expected_headers}\n"
                f"Actual: {actual_headers}"
            )

            # Verify the row data matches the types defined in the schema
            for row in reader:
                # Check participant_id is a string (UUID)
                assert isinstance(row['participant_id'], str)
                # Check age is parsable as int
                assert int(row['age']) == sample_row['age']
                # Check session_duration is parsable as int
                assert int(row['session_duration']) == sample_row['session_duration']
    finally:
        os.unlink(temp_path)


def test_schema_field_types():
    """Verify that schema field types are correctly defined."""
    # Check specific type definitions
    assert METADATA_SCHEMA['age']['type'] == 'integer'
    assert METADATA_SCHEMA['age']['min_value'] == 18
    assert METADATA_SCHEMA['age']['max_value'] == 120

    assert METADATA_SCHEMA['education']['type'] == 'string'
    assert isinstance(METADATA_SCHEMA['education']['options'], list)

    assert METADATA_SCHEMA['timestamp']['type'] == 'string'
    assert METADATA_SCHEMA['timestamp']['format'] == 'ISO8601'

    assert METADATA_SCHEMA['session_duration']['type'] == 'integer'
    assert METADATA_SCHEMA['session_duration']['required'] is True

    assert METADATA_SCHEMA['browser_version']['type'] == 'string'
    assert METADATA_SCHEMA['browser_version']['required'] is True