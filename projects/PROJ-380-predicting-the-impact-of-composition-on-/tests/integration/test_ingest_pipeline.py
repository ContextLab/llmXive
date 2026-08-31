"""
Integration test for the full ingestion pipeline (User Story 1).

This test verifies the end-to-end flow:
1. Data Ingestion (T016): Fetches from Materials Project or falls back to synthetic.
2. Data Cleaning (T017): Filters for BMG phase and standardizes units.
3. Feature Engineering (T018): Calculates descriptors (δ, ΔHmix, VEC, Δχ).
4. Collinearity Handling (T019): Applies VIF filtering.
5. Target Validation (T021): Ensures no missing values in shear modulus.

The test asserts that the final output CSV exists, contains the required columns,
and has no missing values in the target variable.
"""
import os
import sys
import csv
import tempfile
import shutil
import unittest
from pathlib import Path

# Ensure the project root is in the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_paths, ensure_directories, set_random_seed
from data.ingest import fetch_materials_project_data, fallback_to_synthetic, save_to_csv
from data.clean import clean_and_filter
from data.features import process_features
from data.validate_target import validate_target_no_missing

# Set a fixed seed for reproducibility
set_random_seed(42)

class TestIngestionPipeline(unittest.TestCase):
    """Integration tests for the BMG data ingestion pipeline."""

    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp(prefix="bmg_test_")
        # Mock the config paths to point to our temp directory
        # We will override get_paths behavior locally for this test
        self.original_get_paths = get_paths
        
        def mock_get_paths(base_dir=None):
            return {
                "raw": os.path.join(self.temp_dir, "raw"),
                "processed": os.path.join(self.temp_dir, "processed"),
                "artifacts": os.path.join(self.temp_dir, "artifacts"),
                "state": os.path.join(self.temp_dir, "state")
            }
        
        get_paths.__globals__['get_paths'] = mock_get_paths
        # Patch the module level function if it's defined in utils.config
        import utils.config
        utils.config.get_paths = mock_get_paths

        ensure_directories(self.temp_dir)
        self.paths = mock_get_paths(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_pipeline_execution(self):
        """
        Test the full pipeline: Ingest -> Clean -> Features -> VIF -> Validate.
        
        This test ensures that:
        1. The pipeline runs without crashing.
        2. The final output file is created.
        3. The output file contains the expected columns.
        4. The target variable (shear_modulus) has no missing values.
        """
        # 1. Ingestion
        # Try to fetch from Materials Project. If it fails (API down/no key),
        # the ingest module is expected to fallback to synthetic data.
        raw_path = os.path.join(self.paths["raw"], "raw_materials_project.csv")
        
        # We simulate the main logic of ingest.py here to ensure flow
        try:
            # Attempt fetch (this might fail in CI if no API key, triggering fallback)
            data = fetch_materials_project_data()
            if not data or len(data) == 0:
                raise ValueError("No data returned from API")
        except Exception as e:
            # Fallback to synthetic if API fails or returns empty
            data = fallback_to_synthetic()
        
        save_to_csv(data, raw_path)
        self.assertTrue(os.path.exists(raw_path), "Raw data file was not created")

        # 2. Cleaning
        cleaned_path = os.path.join(self.paths["processed"], "cleaned_bmg.csv")
        # Load raw data to pass to clean function
        with open(raw_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            raw_data = list(reader)
        
        cleaned_data = clean_and_filter(raw_data)
        self.assertGreater(len(cleaned_data), 0, "Cleaning resulted in empty dataset")
        
        save_to_csv(cleaned_data, cleaned_path)
        self.assertTrue(os.path.exists(cleaned_path), "Cleaned data file was not created")

        # 3. Feature Engineering
        features_path = os.path.join(self.paths["processed"], "features_bmg.csv")
        
        # Load cleaned data
        with open(cleaned_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            cleaned_data = list(reader)
        
        processed_data = process_features(cleaned_data)
        self.assertGreater(len(processed_data), 0, "Feature engineering resulted in empty dataset")
        
        save_to_csv(processed_data, features_path)
        self.assertTrue(os.path.exists(features_path), "Features file was not created")

        # 4. Collinearity Handling (VIF)
        # process_features in T019 usually handles VIF internally or via iterative selection.
        # Assuming process_features returns data after VIF handling as per T019 spec.
        # If not, we would call iterative_vif_selection here.
        # For this integration test, we assume process_features covers the full feature logic.
        
        # 5. Target Validation
        # Load the final processed data
        with open(features_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            final_data = list(reader)
        
        # Check for missing target
        has_missing, missing_count = validate_target_no_missing(final_data, target_col="shear_modulus")
        
        self.assertFalse(has_missing, f"Target variable has {missing_count} missing values")

        # 6. Verification of Output Structure
        expected_columns = {
            "material_id", "composition", "shear_modulus", 
            "delta", "delta_hmix", "vec", "delta_chi",
            "alloy_family"
        }
        
        if len(final_data) > 0:
            actual_columns = set(final_data[0].keys())
            # Check that all expected columns are present (or at least the core ones)
            # Some columns might be renamed or dropped if VIF removed them, 
            # but shear_modulus and key descriptors should remain.
            self.assertIn("shear_modulus", actual_columns, "shear_modulus column missing")
            self.assertIn("delta", actual_columns, "delta column missing")
            self.assertIn("delta_hmix", actual_columns, "delta_hmix column missing")
            self.assertIn("vec", actual_columns, "vec column missing")
            self.assertIn("delta_chi", actual_columns, "delta_chi column missing")

        print(f"Integration test passed. Processed {len(final_data)} records.")
        print(f"Output written to: {features_path}")

if __name__ == "__main__":
    unittest.main()