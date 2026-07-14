"""
Unit tests for the ``data/preprocess.py`` module.

The tests verify that the preprocessing pipeline can:
  * Create required directories,
  * Detect an existing raw CSV,
  * Download the fallback dataset when no raw file is present,
  * Map fallback columns to the required schema,
  * Produce a ``trial_data.csv`` file with the correct columns.
"""

import os
import shutil
import unittest
from pathlib import Path

import pandas as pd

# Import the module under test
from data.preprocess import (
    PROJECT_ROOT,
    RAW_DIR,
    DERIVED_DIR,
    setup_directories,
    find_input_file,
    download_fallback_dataset,
    load_and_clean_data,
    map_fallback_columns,
    extract_trial_data,
    write_output,
)

class TestPreprocess(unittest.TestCase):
    """Test suite for the preprocessing utilities."""

    @classmethod
    def setUpClass(cls):
        """Create a clean temporary project structure."""
        # Ensure a fresh environment for each test run
        if RAW_DIR.exists():
            shutil.rmtree(RAW_DIR)
        if DERIVED_DIR.exists():
            shutil.rmtree(DERIVED_DIR)

        setup_directories()

    def tearDown(self):
        """Remove any files created during a test."""
        for p in RAW_DIR.glob("*"):
            p.unlink()
        for p in DERIVED_DIR.glob("*"):
            p.unlink()

    def test_find_input_file_none(self):
        """When no CSV is present, ``find_input_file`` should return None."""
        self.assertIsNone(find_input_file())

    def test_download_fallback_dataset(self):
        """The fallback dataset should be downloaded and readable."""
        fallback_path = download_fallback_dataset()
        self.assertTrue(fallback_path.exists())
        df = pd.read_csv(fallback_path)
        # The Iris dataset has at least 5 rows and the expected columns
        self.assertGreaterEqual(df.shape[0], 5)
        self.assertIn("sepal_length", df.columns)

    def test_full_preprocess_creates_trial_file(self):
        """
        Run the full pipeline (using the fallback) and verify that the output
        ``trial_data.csv`` contains the required columns.
        """
        # Ensure no raw CSV exists so the fallback will be used
        for p in RAW_DIR.glob("*"):
            p.unlink()

        # Run the pipeline steps manually (mirroring ``main``)
        raw_path = find_input_file()
        self.assertIsNone(raw_path)  # no raw data yet

        raw_path = download_fallback_dataset()
        df_raw = load_and_clean_data(raw_path)

        # The fallback does not contain the required columns initially
        with self.assertRaises(ValueError):
            # This will raise because ``confidence_rating`` etc. are missing
            from data.preprocess import validate_required_columns

            validate_required_columns(df_raw)

        # Map columns and re‑validate
        df_mapped = map_fallback_columns(df_raw)
        from data.preprocess import validate_required_columns

        # Should not raise now
        validate_required_columns(df_mapped)

        trial_df = extract_trial_data(df_mapped)
        write_output(trial_df)

        output_path = DERIVED_DIR / "trial_data.csv"
        self.assertTrue(output_path.is_file())

        df_out = pd.read_csv(output_path)
        expected_cols = [
            "participant_id",
            "trial_id",
            "stimulus_modality",
            "source_label",
            "participant_response",
            "confidence_rating",
        ]
        self.assertListEqual(list(df_out.columns), expected_cols)

if __name__ == "__main__":
    unittest.main()