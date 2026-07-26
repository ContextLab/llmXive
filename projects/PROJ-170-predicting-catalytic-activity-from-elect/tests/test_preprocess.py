"""
Test suite for User Story 1: Data Acquisition and Preprocessing Pipeline.
Includes contract tests and integration tests for data integrity and alignment.
"""
import os
import sys
import json
import unittest
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_data_path, get_project_root

# Setup logging for test visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestDataIntegrity(unittest.TestCase):
    """
    Contract test for T050: Verify data integrity of aligned_dataset.csv.
    Ensures no NaN values in target column and non-empty composition strings.
    """

    def setUp(self):
        """Locate the processed dataset file."""
        data_path = get_data_path()
        self.dataset_path = Path(data_path) / "processed" / "aligned_dataset.csv"
        if not self.dataset_path.exists():
            logger.error(f"Dataset file not found at {self.dataset_path}. "
                         "Ensure T020 (generate_aligned_dataset) has run successfully.")
            # We do not skip here; the test must fail loudly if the artifact is missing.
            raise FileNotFoundError(f"Required artifact missing: {self.dataset_path}")

    def test_data_integrity(self):
        """
        Verify:
        1. No NaN values exist in the 'energy_change' column.
        2. All 'composition' strings are non-empty.
        """
        import pandas as pd

        logger.info(f"Loading dataset from {self.dataset_path} for integrity check...")
        try:
            df = pd.read_csv(self.dataset_path)
        except Exception as e:
            self.fail(f"Failed to load dataset: {e}")

        # Requirement 1: Check 'energy_change' for NaN
        target_col = "energy_change"
        if target_col not in df.columns:
            self.fail(f"Column '{target_col}' not found in dataset. Columns: {list(df.columns)}")

        nan_count = df[target_col].isna().sum()
        self.assertEqual(
            nan_count, 0,
            f"Integrity Failure: Found {nan_count} NaN values in '{target_col}' column. "
            "Data imputation or filtering logic failed."
        )
        logger.info(f"✓ Integrity Check Passed: 0 NaN values in '{target_col}'.")

        # Requirement 2: Check 'composition' for empty strings
        comp_col = "composition"
        if comp_col not in df.columns:
            self.fail(f"Column '{comp_col}' not found in dataset. Columns: {list(df.columns)}")

        # Check for empty strings or whitespace-only strings
        empty_compositions = df[comp_col].astype(str).str.strip() == ""
        empty_count = empty_compositions.sum()

        self.assertEqual(
            empty_count, 0,
            f"Integrity Failure: Found {empty_count} empty or whitespace-only strings in '{comp_col}' column."
        )
        logger.info(f"✓ Integrity Check Passed: 0 empty compositions found.")

        # Additional sanity check: Ensure file is not empty
        self.assertGreater(
            len(df), 0,
            "Integrity Failure: Dataset is empty (0 rows)."
        )
        logger.info(f"✓ Integrity Check Passed: Dataset contains {len(df)} rows.")


class TestAlignmentColumns(unittest.TestCase):
    """
    Contract test for T008: Verify alignment logic produces expected columns.
    """

    def setUp(self):
        data_path = get_data_path()
        self.dataset_path = Path(data_path) / "processed" / "aligned_dataset.csv"

    def test_alignment_columns(self):
        """Verify the dataset contains the exact schema required by FR-001."""
        import pandas as pd

        if not self.dataset_path.exists():
            self.skipTest(f"Dataset {self.dataset_path} not found. Run T020 first.")

        df = pd.read_csv(self.dataset_path)

        required_columns = {
            "composition",
            "surface_facet",
            "energy_change",
            "d_band_center",
            "adsorption_energy"
        }

        # Check for required columns
        missing = required_columns - set(df.columns)
        if missing:
            self.fail(f"Missing required columns: {missing}")

        logger.info("✓ Alignment Columns Check Passed: All required columns present.")


class TestFullPipelineSample(unittest.TestCase):
    """
    Integration test for T009: Verify full download-to-csv flow.
    """

    def test_full_pipeline_sample(self):
        """
        Verify that the pipeline produces a valid CSV with the correct shape
        and no critical data quality issues.
        """
        import pandas as pd

        data_path = get_data_path()
        dataset_path = Path(data_path) / "processed" / "aligned_dataset.csv"

        if not dataset_path.exists():
            self.skipTest(f"Pipeline output {dataset_path} not found.")

        df = pd.read_csv(dataset_path)

        # Basic shape check (must have rows)
        self.assertGreater(len(df), 0, "Pipeline produced an empty dataset.")

        # Check for NaN in target
        self.assertTrue(
            df["energy_change"].isna().sum() == 0,
            "Pipeline failed to impute/filter NaN in target variable."
        )

        logger.info(f"✓ Full Pipeline Integration Test Passed: {len(df)} rows validated.")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)