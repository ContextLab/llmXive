"""
Unit tests for T020d: Verify that every row in data/provenance_log.csv
contains URL, repository identifier, and fetch timestamp.
"""
import csv
import os
import unittest
from pathlib import Path

REQUIRED_COLUMNS = {"url", "repository_identifier", "fetch_timestamp"}
DATA_PATH = Path("data/provenance_log.csv")


class TestProvenanceSchema(unittest.TestCase):
    """Tests to ensure provenance_log.csv schema compliance."""

    def test_file_exists(self):
        """Verify that data/provenance_log.csv exists on disk."""
        self.assertTrue(
            DATA_PATH.exists(),
            f"File {DATA_PATH} does not exist. Run T020c to generate it."
        )

    def test_file_not_empty(self):
        """Verify that the file contains at least one data row."""
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertGreater(
            len(rows), 0,
            "provenance_log.csv is empty. Expected at least one record."
        )

    def test_required_columns_present(self):
        """Verify that the header contains all required columns."""
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.assertIsNotNone(reader.fieldnames)
            header_set = set(reader.fieldnames)
            missing = REQUIRED_COLUMNS - header_set
            self.assertEqual(
                len(missing), 0,
                f"Missing required columns in header: {missing}. "
                f"Expected columns: {REQUIRED_COLUMNS}"
            )

    def test_all_rows_have_required_fields(self):
        """Verify that every row has non-empty values for required columns."""
        row_count = 0
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                for col in REQUIRED_COLUMNS:
                    value = row.get(col)
                    self.assertIsNotNone(
                        value,
                        f"Row {row_count}: Column '{col}' is missing (None)."
                    )
                    self.assertNotEqual(
                        value.strip(), "",
                        f"Row {row_count}: Column '{col}' is empty."
                    )

    def test_timestamp_format(self):
        """Verify that fetch_timestamp values are valid ISO format strings."""
        import re
        # ISO 8601 basic pattern: YYYY-MM-DDTHH:MM:SS or with microseconds
        iso_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
        )

        row_count = 0
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                ts = row.get("fetch_timestamp", "").strip()
                self.assertRegex(
                    ts,
                    iso_pattern,
                    f"Row {row_count}: fetch_timestamp '{ts}' is not in ISO 8601 format."
                )

    def test_url_validity(self):
        """Verify that URL fields look like valid URLs."""
        import re
        url_pattern = re.compile(r"^https?://")

        row_count = 0
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                url = row.get("url", "").strip()
                self.assertRegex(
                    url,
                    url_pattern,
                    f"Row {row_count}: URL '{url}' does not start with http:// or https://"
                )


if __name__ == "__main__":
    unittest.main()