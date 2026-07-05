import csv
import os
import sys
from pathlib import Path
import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

REQUIRED_FIELDS = {"url", "repository_identifier", "fetch_timestamp"}

def test_provenance_log_exists():
    """Verify that data/provenance_log.csv exists."""
    path = PROJECT_ROOT / "data" / "provenance_log.csv"
    assert path.exists(), f"File missing: {path}"

def test_provenance_log_has_required_columns():
    """Verify that every row in data/provenance_log.csv contains URL, repository identifier, and fetch timestamp."""
    path = PROJECT_ROOT / "data" / "provenance_log.csv"
    assert path.exists(), f"File missing: {path}"

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Check header contains required fields
        if reader.fieldnames is None:
            raise AssertionError("CSV file is empty or has no header")
        
        header_set = set(reader.fieldnames)
        missing_in_header = REQUIRED_FIELDS - header_set
        assert not missing_in_header, f"Missing required columns in header: {missing_in_header}"

        row_count = 0
        for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            row_count += 1
            for field in REQUIRED_FIELDS:
                value = row.get(field)
                if value is None or value.strip() == "":
                    raise AssertionError(
                        f"Row {row_num} is missing or empty for required field '{field}'"
                    )
        
        assert row_count > 0, "CSV file has no data rows"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
