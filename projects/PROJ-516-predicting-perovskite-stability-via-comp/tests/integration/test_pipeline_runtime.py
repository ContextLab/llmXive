"""
Integration test for full pipeline runtime (Task T019).

Verifies that the entire pipeline (Data Ingestion -> Feature Engineering -> 
Filtering -> VIF Diagnostics -> Finalization -> Model Training) completes 
within the 6-hour wall-clock budget.

This test imports and executes the main entry points of the production modules
defined in the code/ directory.
"""
import logging
import os
import sys
import time
import unittest
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from data_ingestion import main as main_data_ingestion
from feature_engineering import main as main_feature_engineering
from filter_descriptors import main as main_filter_descriptors
from vif_diagnostic import main as main_vif_diagnostic
from finalize_descriptors import main as main_finalize_descriptors
from model_training import main as main_model_training

# Configure logging to capture pipeline output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "pipeline_runtime_test.log")
    ]
)
logger = logging.getLogger(__name__)

# Define the 6-hour limit in seconds
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 21600 seconds

class TestPipelineRuntime(unittest.TestCase):
    """
    Integration test to validate the full pipeline execution time.
    """

    def test_full_pipeline_runtime(self):
        """
        Runs the full pipeline and asserts it completes within 6 hours.
        
        Steps:
        1. Data Ingestion (T012)
        2. Feature Engineering (T014)
        3. Filtering (T015)
        4. VIF Diagnostics (T016)
        5. Finalization (T017)
        6. Model Training (T020)
        
        Expected: Total time <= 21600 seconds.
        """
        logger.info(f"Starting full pipeline runtime test at {datetime.now()}")
        logger.info(f"Maximum allowed runtime: {MAX_RUNTIME_SECONDS} seconds (6 hours)")
        
        start_time = time.time()
        pipeline_steps = [
            ("Data Ingestion", main_data_ingestion),
            ("Feature Engineering", main_feature_engineering),
            ("Filtering Descriptors", main_filter_descriptors),
            ("VIF Diagnostics", main_vif_diagnostic),
            ("Finalize Descriptors", main_finalize_descriptors),
            ("Model Training", main_model_training),
        ]

        try:
            for step_name, step_func in pipeline_steps:
                step_start = time.time()
                logger.info(f"Executing step: {step_name}")
                
                # Execute the step's main function
                # Note: These functions are designed to run as scripts and return None
                # upon successful completion or raise exceptions on failure.
                step_func()
                
                step_duration = time.time() - step_start
                logger.info(f"Step '{step_name}' completed in {step_duration:.2f} seconds")

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Pipeline failed during execution after {elapsed:.2f} seconds: {e}")
            self.fail(f"Pipeline execution failed: {e}")

        total_duration = time.time() - start_time
        logger.info(f"Full pipeline completed in {total_duration:.2f} seconds")

        # Assert the runtime constraint
        self.assertLessEqual(
            total_duration, 
            MAX_RUNTIME_SECONDS, 
            f"Pipeline exceeded 6-hour limit. Took {total_duration:.2f} seconds."
        )

        # Log success
        logger.info("SUCCESS: Full pipeline runtime is within the 6-hour constraint.")

    def test_artifacts_exist(self):
        """
        Verifies that the expected output artifacts exist after the pipeline run.
        This ensures the pipeline not only ran fast but produced the required data.
        """
        required_artifacts = [
            PROJECT_ROOT / "data" / "raw" / "nrel_perovskites.csv",
            PROJECT_ROOT / "data" / "raw" / "metadata.json",
            PROJECT_ROOT / "data" / "raw" / "uncertainty_flags.json",
            PROJECT_ROOT / "data" / "processed" / "descriptors.csv",
            PROJECT_ROOT / "data" / "processed" / "vif_report.csv",
            PROJECT_ROOT / "data" / "processed" / "model_runs.json",
        ]

        missing = []
        for artifact in required_artifacts:
            if not artifact.exists():
                missing.append(str(artifact))

        if missing:
            self.fail(f"Missing required artifacts after pipeline run: {missing}")
        
        logger.info("All required artifacts verified.")

if __name__ == "__main__":
    unittest.main(verbosity=2)