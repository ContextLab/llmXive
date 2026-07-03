"""
Integration test for the full User Story 1 preprocessing pipeline.

This test verifies the end-to-end flow:
1. Generate synthetic test data (flagged for unit tests only).
2. Load data using code/preprocessing/load_data.py.
3. Preprocess (filter) using code/preprocessing/filter.py.
4. Extract features using code/preprocessing/features.py.
5. Compute correlations using code/analysis/correlations.py.

It asserts that:
- All intermediate and final output files are created in expected locations.
- Output CSVs contain required columns.
- Statistical results (Pearson r, p-values) are numeric and within valid ranges.
- Quality report is updated correctly.
"""
import os
import sys
import unittest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from generate_synthetic_test_data import generate_synthetic_dataset
from preprocessing.load_data import load_raw_eye_tracking
from preprocessing.filter import preprocess_pipeline
from preprocessing.features import extract_load_proxies
from analysis.correlations import compute_correlations
from data_model import Dataset

# Ensure paths match project structure
RAW_DATA_DIR = project_root / "data" / "raw"
PROCESSED_DATA_DIR = project_root / "data" / "processed"
RESULTS_DIR = project_root / "results"
STATE_DIR = project_root / "state"

class TestUS1PreprocessingPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """
        Setup: Ensure directories exist and generate synthetic test data.
        This simulates the output of T002d but integrated into the pipeline test.
        """
        # Create necessary directories if they don't exist
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        STATE_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize quality report if it doesn't exist (T005 responsibility)
        quality_report_path = RESULTS_DIR / "quality_report.csv"
        if not quality_report_path.exists():
            pd.DataFrame(columns=["exclusion_type", "count"]).to_csv(
                quality_report_path, index=False
            )

        # Generate synthetic test data
        # We use a specific seed for reproducibility
        cls.test_seed = 42
        cls.subject_id = "SUBJ_001"
        cls.trial_count = 50
        
        synthetic_file_path = generate_synthetic_dataset(
            output_dir=str(RAW_DATA_DIR),
            subject_id=cls.subject_id,
            trial_count=cls.trial_count,
            seed=cls.test_seed,
            test_mode=True
        )
        cls.raw_file_path = synthetic_file_path
        
        # Define output paths for this test run
        cls.processed_file_path = PROCESSED_DATA_DIR / f"{cls.subject_id}_processed.csv"
        cls.features_file_path = PROCESSED_DATA_DIR / f"{cls.subject_id}_features.csv"
        cls.correlations_file_path = RESULTS_DIR / "correlations.csv"
        cls.quality_report_path = RESULTS_DIR / "quality_report.csv"

    def test_01_load_raw_data(self):
        """Test that raw data is loaded successfully into a DataFrame."""
        self.assertTrue(self.raw_file_path.exists(), "Raw test data file not found.")
        
        df = load_raw_eye_tracking(self.raw_file_path)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0, "Loaded data is empty.")
        
        required_cols = ["timestamp", "x", "y", "pupil_diameter"]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

    def test_02_preprocess_pipeline(self):
        """Test the filtering pipeline: blink interpolation and low-pass filter."""
        # Ensure raw data exists
        if not self.raw_file_path.exists():
            self.skipTest("Raw data file missing for preprocessing test.")

        # Run preprocessing
        df_processed = preprocess_pipeline(
            input_path=str(self.raw_file_path),
            output_path=str(self.processed_file_path)
        )

        # Assertions
        self.assertTrue(self.processed_file_path.exists(), "Processed file not written.")
        self.assertIsInstance(df_processed, pd.DataFrame)
        self.assertGreater(len(df_processed), 0, "Processed data is empty.")
        
        # Check that processed data has same core columns
        required_cols = ["timestamp", "x", "y", "pupil_diameter"]
        for col in required_cols:
            self.assertIn(col, df_processed.columns)

        # Verify quality report was updated
        self.assertTrue(self.quality_report_path.exists(), "Quality report not found.")
        report_df = pd.read_csv(self.quality_report_path)
        self.assertIn("exclusion_type", report_df.columns)
        self.assertIn("count", report_df.columns)

    def test_03_extract_load_proxies(self):
        """Test feature extraction: search time, fixation count, target salience."""
        if not self.processed_file_path.exists():
            # Run previous step if needed
            preprocess_pipeline(str(self.raw_file_path), str(self.processed_file_path))

        df_features = extract_load_proxies(
            input_path=str(self.processed_file_path),
            output_path=str(self.features_file_path),
            subject_id=self.subject_id
        )

        self.assertTrue(self.features_file_path.exists(), "Features file not written.")
        self.assertIsInstance(df_features, pd.DataFrame)
        
        # Required columns from T015
        required_cols = ["timestamp", "search_time", "fixation_count", "target_salience"]
        for col in required_cols:
            self.assertIn(col, df_features.columns, f"Missing feature column: {col}")

        # Check for UNFULFILLABLE status if applicable (though synthetic data should be valid)
        if "status" in df_features.columns:
            # If status exists, it should be either 'VALID' or 'UNFULFILLABLE'
            valid_statuses = ["VALID", "UNFULFILLABLE"]
            for status in df_features["status"].unique():
                self.assertIn(status, valid_statuses)

    def test_04_compute_correlations(self):
        """Test correlation analysis: Pearson r, p-values, FDR correction."""
        if not self.features_file_path.exists():
            # Run previous steps if needed
            preprocess_pipeline(str(self.raw_file_path), str(self.processed_file_path))
            extract_load_proxies(str(self.processed_file_path), str(self.features_file_path), self.subject_id)

        results_df = compute_correlations(
            input_path=str(self.features_file_path),
            output_path=str(self.correlations_file_path)
        )

        self.assertTrue(self.correlations_file_path.exists(), "Correlations file not written.")
        self.assertIsInstance(results_df, pd.DataFrame)
        
        # Required columns from T016
        required_cols = ["correlation_type", "variable", "pearson_r", "p_value", "p_value_fdr"]
        for col in required_cols:
            self.assertIn(col, results_df.columns, f"Missing correlation column: {col}")

        # Validate numeric ranges
        # Pearson r should be between -1 and 1
        if "pearson_r" in results_df.columns:
            self.assertTrue(results_df["pearson_r"].between(-1, 1).all(), "Pearson r out of range [-1, 1]")
        
        # p-values should be between 0 and 1
        for p_col in ["p_value", "p_value_fdr"]:
            if p_col in results_df.columns:
                self.assertTrue(results_df[p_col].between(0, 1).all(), f"{p_col} out of range [0, 1]")

    def test_05_full_pipeline_integration(self):
        """
        End-to-end integration test:
        Run the entire US1 pipeline on the synthetic dataset and verify final outputs.
        """
        # 1. Load
        df_raw = load_raw_eye_tracking(str(self.raw_file_path))
        self.assertGreater(len(df_raw), 0)

        # 2. Preprocess
        df_clean = preprocess_pipeline(str(self.raw_file_path), str(self.processed_file_path))
        self.assertGreater(len(df_clean), 0)
        self.assertTrue(self.processed_file_path.exists())

        # 3. Features
        df_feat = extract_load_proxies(str(self.processed_file_path), str(self.features_file_path), self.subject_id)
        self.assertGreater(len(df_feat), 0)
        self.assertTrue(self.features_file_path.exists())

        # 4. Correlations
        df_corr = compute_correlations(str(self.features_file_path), str(self.correlations_file_path))
        self.assertGreater(len(df_corr), 0)
        self.assertTrue(self.correlations_file_path.exists())

        # 5. Final Assertions on Content
        # Check quality report has entries
        q_report = pd.read_csv(self.quality_report_path)
        self.assertGreater(len(q_report), 0)

        # Check correlations have valid FDR corrected values
        self.assertIn("p_value_fdr", df_corr.columns)
        self.assertTrue(df_corr["p_value_fdr"].notna().all())

if __name__ == "__main__":
    unittest.main()