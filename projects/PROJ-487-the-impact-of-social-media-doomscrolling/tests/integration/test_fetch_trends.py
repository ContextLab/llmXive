import pytest
import os
import csv
from pathlib import Path
import sys
from datetime import datetime

# Ensure code directory is in path
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from fetch_data import fetch_trends_anxiety

@pytest.fixture
def sample_dates():
    # Use a recent range to ensure data availability for integration test
    # Avoiding very old dates which might be rate-limited or unavailable
    today = datetime.now()
    end = today.strftime("%Y-%m-%d")
    start = (today.replace(year=today.year - 1)).strftime("%Y-%m-%d")
    return start, end

@pytest.mark.integration
def test_fetch_trends_non_empty_csv(sample_dates, tmp_path):
    """
    Integration test verifying non-empty CSV generation for Google Trends.
    """
    start_date, end_date = sample_dates
    output_path = tmp_path / "trends_test.csv"

    # Execute fetch
    result = fetch_trends_anxiety(start_date, end_date, output_path)

    # Assert fetch function returned success
    assert result is True, "Fetch function should return True"

    # Assert file exists
    assert output_path.exists(), "Output CSV file should exist"

    # Assert file is not empty (has headers and at least one data row)
    with open(output_path, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) > 1, "CSV should contain at least one data row beyond header"
    
    # Validate header
    header = rows[0]
    assert header == ['date', 'value', 'source'], f"Header mismatch: {header}"

    # Validate data types in first data row
    first_row = rows[1]
    assert len(first_row) == 3, "Row should have 3 columns"
    
    # Check date format
    try:
        datetime.strptime(first_row[0], '%Y-%m-%d')
    except ValueError:
        pytest.fail(f"Date format invalid: {first_row[0]}")

    # Check value is numeric
    try:
        float(first_row[1])
    except ValueError:
        pytest.fail(f"Value is not numeric: {first_row[1]}")

    # Check source is present
    assert first_row[2] == "Google Trends", f"Source mismatch: {first_row[2]}"