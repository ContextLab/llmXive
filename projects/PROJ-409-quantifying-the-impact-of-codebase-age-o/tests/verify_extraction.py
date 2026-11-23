import csv
import os
import sys
import unittest
from pathlib import Path

# Ensure code/ is in path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from extraction.verify_extraction import verify_csv_structure, REQUIRED_COLUMNS, MIN_ROW_COUNT

class TestExtractionVerification(unittest.TestCase):
    def setUp(self):
        self.csv_path = Path("data/extracted/snippets.csv")

    def test_csv_exists(self):
        """Assert the extraction CSV file exists."""
        self.assertTrue(self.csv_path.exists(), "Extraction CSV file must exist")

    def test_required_columns_exist(self):
        """Assert all required columns are present in the CSV."""
        self.assertTrue(self.csv_path.exists(), "CSV must exist before checking columns")

        with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

        missing = REQUIRED_COLUMNS - headers
        self.assertEqual(len(missing), 0, f"Missing columns: {missing}")

    def test_minimum_row_count(self):
        """Assert the CSV has at least the minimum required rows."""
        self.assertTrue(self.csv_path.exists(), "CSV must exist before counting rows")

        with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            row_count = sum(1 for _ in reader)

        self.assertGreaterEqual(row_count, MIN_ROW_COUNT,
                                f"Row count {row_count} is below minimum {MIN_ROW_COUNT}")

    def test_non_null_critical_fields(self):
        """Assert that critical fields are non-null in sampled rows."""
        self.assertTrue(self.csv_path.exists(), "CSV must exist before sampling")

        critical_fields = ["snippet_id", "snippet_content", "repo_url", "file_path"]

        with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 10:  # Sample first 10 rows
                    break
                for field in critical_fields:
                    value = row.get(field, "").strip()
                    self.assertNotEqual(value, "", f"Critical field '{field}' is empty in row {i}")

if __name__ == "__main__":
    unittest.main()