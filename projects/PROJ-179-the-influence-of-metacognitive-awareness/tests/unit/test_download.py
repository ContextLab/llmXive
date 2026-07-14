"""
Unit tests for the data/download module.

The tests verify that the download script creates the expected file,
adds the required columns and writes a checksum entry.
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Ensure the project root is on the import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from data.download import (
    main,
    REQUIRED_COLUMNS,
    CHECKSUM_FILE,
)


class TestDownloadModule(unittest.TestCase):
    """Basic sanity checks for the download routine."""

    def setUp(self):
        # Remove any previous artefacts to guarantee a clean run.
        self.project_root = PROJECT_ROOT
        self.raw_dir = self.project_root / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        self.dest_file = self.raw_dir / "iris_behavioral.csv"
        if self.dest_file.is_file():
            self.dest_file.unlink()

        if CHECKSUM_FILE.is_file():
            CHECKSUM_FILE.unlink()

    def test_main_successful_execution(self):
        """Running ``main`` should exit with code 0 and produce the artefacts."""
        exit_code = main()
        self.assertEqual(exit_code, 0, "main() should return 0 on success")

        # The CSV must exist.
        self.assertTrue(self.dest_file.is_file(), "Dataset file was not created")

        # Verify required columns are present.
        import pandas as pd

        df = pd.read_csv(self.dest_file)
        for col in REQUIRED_COLUMNS:
            self.assertIn(
                col,
                df.columns,
                f"Required column '{col}' missing after download augmentation",
            )

        # Verify checksum file was written and contains an entry for the CSV.
        self.assertTrue(
            CHECKSUM_FILE.is_file(),
            "Checksum JSON file should be created by the download script",
        )
        with CHECKSUM_FILE.open("r", encoding="utf-8") as f:
            checksums = json.load(f)
        self.assertIn(
            self.dest_file.name,
            checksums,
            "Checksum mapping for the downloaded file is missing",
        )

    def tearDown(self):
        # Clean up artefacts created by the test to keep the repo tidy.
        if self.dest_file.is_file():
            self.dest_file.unlink()
        if CHECKSUM_FILE.is_file():
            CHECKSUM_FILE.unlink()


if __name__ == "__main__":
    unittest.main()