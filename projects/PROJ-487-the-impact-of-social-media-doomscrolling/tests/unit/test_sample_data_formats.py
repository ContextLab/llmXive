"""
Unit tests for T008: Verify sample CSV placeholders exist and match expected schema.
These tests ensure CI fallback data is valid before attempting real API fetches.
"""
import csv
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = PROJECT_ROOT / "data" / "raw" / "samples"

GDELT_SAMPLE = SAMPLES_DIR / "gdelt_sentiment_sample.csv"
TRENDS_SAMPLE = SAMPLES_DIR / "trends_anxiety_sample.csv"

def gdelt_schema_validator(row: dict) -> bool:
    """Validates a row against the GDELT sample schema."""
    required = ["date", "value", "source"]
    if not all(k in row for k in required):
        return False
    # Check types
    try:
        float(row["value"])
        return True
    except ValueError:
        return False

def trends_schema_validator(row: dict) -> bool:
    """Validates a row against the Trends sample schema."""
    required = ["date", "value", "source"]
    if not all(k in row for k in required):
        return False
    # Check types
    try:
        float(row["value"])
        return True
    except ValueError:
        return False

@pytest.fixture(scope="module")
def gdelt_rows():
    if not GDELT_SAMPLE.exists():
        pytest.skip(f"Sample file {GDELT_SAMPLE} not found. Run task T008 first.")
    with open(GDELT_SAMPLE, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

@pytest.fixture(scope="module")
def trends_rows():
    if not TRENDS_SAMPLE.exists():
        pytest.skip(f"Sample file {TRENDS_SAMPLE} not found. Run task T008 first.")
    with open(TRENDS_SAMPLE, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

class TestGDELTSampleFormat:
    def test_file_exists(self):
        assert GDELT_SAMPLE.exists(), "GDELT sample file must exist"

    def test_has_header(self, gdelt_rows):
        assert len(gdelt_rows) > 0, "Sample file must have at least one row"
        assert "date" in gdelt_rows[0]
        assert "value" in gdelt_rows[0]
        assert "source" in gdelt_rows[0]

    def test_schema_validation(self, gdelt_rows):
        for i, row in enumerate(gdelt_rows):
            assert gdelt_schema_validator(row), f"Row {i} failed schema validation"

    def test_source_consistency(self, gdelt_rows):
        for row in gdelt_rows:
            assert row["source"] == "GDELT", f"Source must be 'GDELT', got {row['source']}"

class TestTrendsSampleFormat:
    def test_file_exists(self):
        assert TRENDS_SAMPLE.exists(), "Trends sample file must exist"

    def test_has_header(self, trends_rows):
        assert len(trends_rows) > 0, "Sample file must have at least one row"
        assert "date" in trends_rows[0]
        assert "value" in trends_rows[0]
        assert "source" in trends_rows[0]

    def test_schema_validation(self, trends_rows):
        for i, row in enumerate(trends_rows):
            assert trends_schema_validator(row), f"Row {i} failed schema validation"

    def test_source_consistency(self, trends_rows):
        for row in trends_rows:
            assert row["source"] == "GoogleTrends", f"Source must be 'GoogleTrends', got {row['source']}"
