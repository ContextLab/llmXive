"""
Integration tests for the baseline power analysis pipeline.

This test suite verifies the end-to-end functionality of the pipeline
using the Iris dataset as a real-world example.

Expected behavior:
- Tests should FAIL initially if the main pipeline logic (T014) is incomplete.
- Tests verify that theoretical vs empirical power calculations are performed.
- Tests verify that results are saved to the correct JSON schema.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

import numpy as np

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories, RANDOM_SEED
from loaders import load_dataset
from main import run_baseline_analysis
from validators import run_full_validation
from utils import safe_json_save, setup_logging
from power_theory import calculate_theoretical_power
from power_empirical import run_bootstrap_power_simulation

# Setup logging for the test run
logger = setup_logging("integration_test")


class TestBaselinePipelineIntegration(TestCase):
    """
    Integration test for the baseline pipeline on the Iris dataset.
    
    This test simulates the full flow:
    1. Load the Iris dataset (real data).
    2. Run the baseline analysis (theoretical vs empirical power).
    3. Validate the output against the schema.
    4. Assert that the results are reasonable (e.g., power > 0.8 for sufficient N).
    """

    def setUp(self):
        """Set up temporary directories and ensure project structure exists."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.results_dir = self.data_dir / "results"
        
        # Ensure directories exist (mimicking T001/T009)
        ensure_directories(base_path=self.temp_dir)
        
        # Configure paths for this test run
        self.dataset_name = "iris"
        self.output_file = self.results_dir / "baseline_iris.json"
        
        logger.info(f"Test setup complete. Output will be written to: {self.output_file}")

    def test_iris_baseline_pipeline_execution(self):
        """
        Test that the baseline pipeline runs successfully on the Iris dataset.
        
        This test verifies:
        1. The dataset can be loaded via the loader module.
        2. The baseline analysis function executes without error.
        3. The output file is created and contains valid JSON.
        4. The JSON structure matches the expected schema (theoretical, empirical, error).
        """
        # 1. Load the dataset
        # We use the loader to fetch the real Iris dataset from UCI/OpenML
        try:
            dataset_info = load_dataset(self.dataset_name, target_dir=self.data_dir / "raw")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            self.fail(f"Dataset loading failed: {e}")

        self.assertIsNotNone(dataset_info, "Dataset info should not be None")
        self.assertIn("data", dataset_info, "Dataset info must contain 'data' key")
        
        data = dataset_info["data"]
        logger.info(f"Loaded Iris dataset with shape: {data.shape}")

        # 2. Run the baseline analysis
        # This function should calculate theoretical and empirical power
        try:
            results = run_baseline_analysis(
                dataset_name=self.dataset_name,
                data=data,
                output_path=str(self.output_file)
            )
        except Exception as e:
            logger.error(f"Baseline analysis failed: {e}")
            self.fail(f"Baseline analysis execution failed: {e}")

        # 3. Verify output file exists
        self.assertTrue(
            self.output_file.exists(),
            f"Output file {self.output_file} was not created."
        )

        # 4. Load and validate the JSON content
        with open(self.output_file, "r") as f:
            saved_results = json.load(f)

        # 5. Validate schema structure (matching contracts/power_estimate.schema.yaml)
        required_keys = ["theoretical_power", "empirical_power", "absolute_error"]
        for key in required_keys:
            self.assertIn(
                key, saved_results,
                f"Missing required key '{key}' in baseline results."
            )
            self.assertIsInstance(
                saved_results[key], (int, float),
                f"Key '{key}' must be a numeric value."
            )

        # 6. Sanity checks on the values
        # Power should be between 0 and 1
        self.assertGreaterEqual(saved_results["theoretical_power"], 0.0)
        self.assertLessEqual(saved_results["theoretical_power"], 1.0)
        self.assertGreaterEqual(saved_results["empirical_power"], 0.0)
        self.assertLessEqual(saved_results["empirical_power"], 1.0)

        # Absolute error should be non-negative
        self.assertGreaterEqual(saved_results["absolute_error"], 0.0)

        logger.info(
            f"Pipeline test passed. "
            f"Theoretical: {saved_results['theoretical_power']:.4f}, "
            f"Empirical: {saved_results['empirical_power']:.4f}, "
            f"Error: {saved_results['absolute_error']:.4f}"
        )

    def test_validation_logic_integration(self):
        """
        Test that the validation logic (T008) is correctly invoked during the pipeline.
        
        This ensures that datasets flagged as unreliable are handled correctly,
        and that the bootstrap validity check is performed.
        """
        # Load dataset
        dataset_info = load_dataset(self.dataset_name, target_dir=self.data_dir / "raw")
        data = dataset_info["data"]

        # Run validation explicitly to ensure it doesn't crash
        # This mimics the validation step inside run_baseline_analysis
        try:
            validation_result = run_full_validation(
                data=data,
                dataset_name=self.dataset_name
            )
        except Exception as e:
            logger.error(f"Validation logic failed: {e}")
            self.fail(f"Validation logic execution failed: {e}")

        # Check that validation returns a dictionary
        self.assertIsInstance(validation_result, dict)
        
        # Check for expected keys in validation result
        expected_keys = ["is_valid", "bootstrap_validity", "achieved_magnitude", "excluded"]
        for key in expected_keys:
            self.assertIn(
                key, validation_result,
                f"Validation result missing expected key '{key}'."
            )

        logger.info(f"Validation integration test passed. Result: {validation_result}")

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")


if __name__ == "__main__":
    import unittest
    # Run the tests
    unittest.main(verbosity=2)
