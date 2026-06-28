"""
Unit tests for provenance log schema validation (T020d).

This test module verifies that every row in data/provenance_log.csv
contains the required fields: URL, repository identifier, and fetch timestamp.
"""

import csv
import os
from pathlib import Path
import pytest
from datetime import datetime


class TestProvenanceSchema:
    """Test suite for provenance log schema validation."""

    @pytest.fixture
    def provenance_log_path(self):
        """Return the path to the provenance log file."""
        return Path("data/provenance_log.csv")

    @pytest.fixture
    def required_columns(self):
        """Return the set of required column names."""
        return {"url", "repository_identifier", "fetch_timestamp"}

    def test_provenance_log_exists(self, provenance_log_path):
        """Verify that the provenance log file exists."""
        assert provenance_log_path.exists(), (
            f"Provenance log file not found at {provenance_log_path}. "
            "Ensure T020c has archived provenance metadata."
        )

    def test_provenance_log_has_required_columns(self, provenance_log_path, required_columns):
        """Verify that the provenance log has all required columns."""
        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            actual_columns = set(reader.fieldnames or [])

        missing = required_columns - actual_columns
        assert not missing, (
            f"Provenance log missing required columns: {missing}. "
            f"Required: {required_columns}, Found: {actual_columns}"
        )

    def test_all_rows_contain_url(self, provenance_log_path):
        """Verify that every row contains a non-empty URL."""
        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # start=2 for header
                url = row.get("url", "").strip()
                assert url, f"Row {row_num}: URL field is empty or missing"

    def test_all_rows_contain_repository_identifier(self, provenance_log_path):
        """Verify that every row contains a non-empty repository identifier."""
        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # start=2 for header
                repo_id = row.get("repository_identifier", "").strip()
                assert repo_id, f"Row {row_num}: repository_identifier field is empty or missing"

    def test_all_rows_contain_fetch_timestamp(self, provenance_log_path):
        """Verify that every row contains a valid fetch timestamp."""
        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # start=2 for header
                timestamp_str = row.get("fetch_timestamp", "").strip()
                assert timestamp_str, f"Row {row_num}: fetch_timestamp field is empty or missing"

                # Try to parse as ISO format datetime
                try:
                    datetime.fromisoformat(timestamp_str)
                except ValueError:
                    # Also try common formats
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                        try:
                            datetime.strptime(timestamp_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        assert False, (
                            f"Row {row_num}: fetch_timestamp '{timestamp_str}' "
                            "is not a valid ISO or common datetime format"
                        )

    def test_provenance_log_has_at_least_one_row(self, provenance_log_path):
        """Verify that the provenance log contains at least one data row."""
        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0, (
            "Provenance log file exists but contains no data rows. "
            "Ensure T020c has archived at least one provenance record."
        )

    def test_url_field_format(self, provenance_log_path):
        """Verify that URL fields look like valid URLs."""
        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # start=2 for header
                url = row.get("url", "").strip()
                # Basic URL validation: should start with http:// or https://
                assert url.startswith("http://") or url.startswith("https://"), (
                    f"Row {row_num}: URL '{url}' does not appear to be a valid HTTP/HTTPS URL"
                )

    def test_repository_identifier_not_empty(self, provenance_log_path):
        """Verify that repository identifiers are non-empty strings."""
        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # start=2 for header
                repo_id = row.get("repository_identifier", "").strip()
                assert repo_id and len(repo_id) > 0, (
                    f"Row {row_num}: repository_identifier must be a non-empty string"
                )

    def test_fetch_timestamp_is_recent(self, provenance_log_path):
        """Verify that fetch timestamps are reasonably recent (within last 30 days)."""
        thirty_days_ago = datetime.now() - __import__("datetime").timedelta(days=30)

        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # start=2 for header
                timestamp_str = row.get("fetch_timestamp", "").strip()
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

                # Allow timestamps from the past 30 days (for testing purposes)
                assert timestamp >= thirty_days_ago, (
                    f"Row {row_num}: fetch_timestamp '{timestamp_str}' is older than 30 days"
                )

    def test_provenance_log_schema_compliance(self, provenance_log_path, required_columns):
        """
        End-to-end test: verify complete schema compliance.

        This test ensures:
        1. File exists
        2. All required columns are present
        3. Every row has non-empty values for all required columns
        4. URLs are valid HTTP/HTTPS URLs
        5. Timestamps are parseable datetime values
        """
        assert provenance_log_path.exists(), "Provenance log file must exist"

        with open(provenance_log_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])

            # Check required columns
            assert required_columns.issubset(fieldnames), (
                f"Missing required columns: {required_columns - fieldnames}"
            )

            # Validate each row
            valid_row_count = 0
            for row_num, row in enumerate(reader, start=2):
                # Check URL
                assert row.get("url", "").strip().startswith("http"), (
                    f"Row {row_num}: Invalid URL format"
                )

                # Check repository identifier
                assert row.get("repository_identifier", "").strip(), (
                    f"Row {row_num}: Missing repository identifier"
                )

                # Check timestamp
                timestamp_str = row.get("fetch_timestamp", "").strip()
                assert timestamp_str, f"Row {row_num}: Missing fetch timestamp"

                # Try to parse timestamp
                try:
                    datetime.fromisoformat(timestamp_str)
                except ValueError:
                    datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                valid_row_count += 1

            assert valid_row_count > 0, "No valid rows found in provenance log"