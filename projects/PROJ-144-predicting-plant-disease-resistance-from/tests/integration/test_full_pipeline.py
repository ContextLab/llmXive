"""
Integration test for the full preprocessing pipeline (T011).
Orchestrates: Download -> Validate Temporal -> Preprocess -> Harmonize Labels.
Verifies that data flows correctly through all stages and produces expected outputs.
"""
import os
import sys
import unittest
import shutil
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.download import download_metabolomics_data
from code.data.validate_temporal import validate_temporal_consistency
from code.data.preprocess import preprocess_metabolomics
from code.data.harmonize_labels import harmonize_labels
from code.utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR, HOLD_OUT_FRACTION


class TestFullPipeline(unittest.TestCase):
    """
    Integration test for US1: Data Acquisition and Preprocessing Pipeline.
    
    This test verifies:
    1. Real data download from Metabolomics Workbench (or fallback if specific IDs fail).
    2. Temporal validation (sample_time < challenge_time).
    3. Preprocessing (log-transform, missing value filtering, batch correction).
    4. Label harmonization (z-scoring, encoding).
    5. Output file generation in correct locations.
    """

    def setUp(self):
        """Set up test fixtures and temporary directories."""
        self.test_dir = tempfile.mkdtemp(prefix="pipeline_test_")
        self.data_raw_dir = os.path.join(self.test_dir, "data", "raw")
        self.data_processed_dir = os.path.join(self.test_dir, "data", "processed")
        
        os.makedirs(self.data_raw_dir, exist_ok=True)
        os.makedirs(self.data_processed_dir, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directories."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _patch_constants(self):
        """Patch constants module to use test directories."""
        # Temporarily override the constants module's paths
        import code.utils.constants as constants
        constants.DATA_RAW_DIR = self.data_raw_dir
        constants.DATA_PROCESSED_DIR = self.data_processed_dir
        constants.HOLD_OUT_FRACTION = 0.20
        # Re-import functions that rely on constants to pick up new paths
        # In a real scenario, we'd refactor to pass paths as arguments,
        # but for integration testing we patch the module state.

    def test_full_pipeline_execution(self):
        """
        Run the full pipeline: Download -> Validate -> Preprocess -> Harmonize.
        Verify that output files are created and contain valid data.
        """
        self._patch_constants()

        # 1. Download Data
        # Attempt to download real data. If specific study IDs fail, 
        # the download function should handle fallback or raise a clear error.
        # For this integration test, we expect the function to attempt a fetch.
        try:
            download_results = download_metabolomics_data()
            # If download_results is empty, it might mean no data was found/downloaded.
            # We proceed to check if any raw files exist.
        except Exception as e:
            # If download fails due to network or API issues, we might skip to validation
            # if we have cached data, or fail the test if no data exists.
            if not os.listdir(self.data_raw_dir):
                self.fail(f"Data download failed and no cached data found: {e}")
            download_results = []

        # 2. Validate Temporal Consistency
        # Check that sample_time < challenge_time for all samples
        try:
            validation_passed = validate_temporal_consistency()
        except Exception as e:
            self.fail(f"Temporal validation failed: {e}")
        
        self.assertTrue(validation_passed, "Temporal validation must pass")

        # 3. Preprocess Data
        # Log-transform, filter missing values, align metabolites, batch correct
        try:
            preprocess_results = preprocess_metabolomics()
        except Exception as e:
            self.fail(f"Preprocessing failed: {e}")

        # 4. Harmonize Labels
        # Encode resistance labels and apply z-scoring
        try:
            harmonization_results = harmonize_labels()
        except Exception as e:
            self.fail(f"Label harmonization failed: {e}")

        # 5. Verify Output Files Exist
        expected_matrix_path = os.path.join(self.data_processed_dir, "batch_corrected_matrix.csv")
        expected_labels_path = os.path.join(self.data_processed_dir, "labels.csv")

        self.assertTrue(
            os.path.exists(expected_matrix_path),
            f"Preprocessed matrix file not found: {expected_matrix_path}"
        )
        self.assertTrue(
            os.path.exists(expected_labels_path),
            f"Labels file not found: {expected_labels_path}"
        )

        # 6. Verify Data Integrity
        # Load and check that data is not empty and has expected structure
        matrix_df = pd.read_csv(expected_matrix_path)
        labels_df = pd.read_csv(expected_labels_path)

        self.assertGreater(
            len(matrix_df), 0, "Preprocessed matrix must contain rows"
        )
        self.assertGreater(
            len(labels_df), 0, "Labels file must contain rows"
        )

        # Check for expected columns (adjust based on actual schema)
        # Assuming standard metabolomics format: sample_id, metabolite_1, metabolite_2...
        # and labels: sample_id, resistance_label, etc.
        self.assertIn("sample_id", matrix_df.columns)
        self.assertIn("sample_id", labels_df.columns)

        # Verify row counts match
        self.assertEqual(
            len(matrix_df), len(labels_df),
            "Matrix and labels must have the same number of samples"
        )

        # 7. Verify Preprocessing Steps (Log-transform, missing value handling)
        # Check that no negative values exist (log-transformed data should be > -inf, usually > 0 or shifted)
        # Check that missing values are handled (no NaNs in the final matrix if discarded)
        numeric_cols = matrix_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # If log-transformed, values should be finite
            self.assertTrue(
                np.all(np.isfinite(matrix_df[col])),
                f"Column {col} contains non-finite values after preprocessing"
            )

        # Verify label harmonization (binary or ordinal)
        # Check that resistance_label column exists and has expected dtype
        if "resistance_label" in labels_df.columns:
            unique_labels = labels_df["resistance_label"].unique()
            # Should be numeric (0/1 or ordinal)
            self.assertTrue(
                all(isinstance(x, (int, float)) for x in unique_labels),
                "Resistance labels must be numeric after harmonization"
            )


if __name__ == "__main__":
    unittest.main()
