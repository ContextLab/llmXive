"""
Integration Test T013: Baseline Pipeline.

Runs the full baseline pipeline: ingestion -> descriptors -> training -> report.
Validates that the pipeline executes without errors and produces the expected outputs
(specifically checking for MAE in the baseline report).
"""
import os
import sys
import unittest
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestBaselinePipeline(unittest.TestCase):
    """Integration test for the baseline pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.results_dir = Path("results")
        self.data_processed_dir = Path("data/processed")
        self.artifacts_dir = Path("artifacts")
        
        # Ensure directories exist
        self.results_dir.mkdir(exist_ok=True)
        self.data_processed_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)

    def test_pipeline_imports(self):
        """Test that all required pipeline modules can be imported."""
        try:
            from ingestion import main as ingestion_main
            from descriptors import main as descriptors_main
            from training import main as training_main
            logger.info("All pipeline modules imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import pipeline modules: {e}")

    def test_pipeline_execution_structure(self):
        """Test the structure of the pipeline execution."""
        from ingestion import main as ingestion_main
        from descriptors import main as descriptors_main
        from training import main as training_main
        
        self.assertTrue(callable(ingestion_main), "ingestion.main must be callable.")
        self.assertTrue(callable(descriptors_main), "descriptors.main must be callable.")
        self.assertTrue(callable(training_main), "training_main must be callable.")
        
        logger.info("Pipeline functions are callable.")

    def test_full_pipeline_mae_output(self):
        """
        Execute the full baseline pipeline end-to-end and verify MAE output.
        
        This test runs the actual pipeline components in sequence:
        1. Ingestion (fetches/merges data, saves to data/processed)
        2. Descriptors (computes Magpie features, saves to data/processed)
        3. Training (trains RF/GB, evaluates, saves to results)
        
        It asserts that the final `results/baseline_report.csv` exists and contains
        a column named 'MAE' with at least one numeric value, proving the pipeline
        produced real metrics.
        """
        logger.info("Starting full baseline pipeline execution test...")
        
        # 1. Run Ingestion
        logger.info("Step 1: Running Ingestion...")
        try:
            from ingestion import main as ingestion_main
            # We call main() directly. Note: If data is missing, this will attempt to fetch.
            # The task requires real data; if fetch fails, it should raise an error (Fail Loudly).
            ingestion_main()
            logger.info("Ingestion completed successfully.")
        except Exception as e:
            self.fail(f"Ingestion failed: {e}")

        # 2. Run Descriptors
        logger.info("Step 2: Running Descriptor Computation...")
        try:
            from descriptors import main as descriptors_main
            descriptors_main()
            logger.info("Descriptor computation completed successfully.")
        except Exception as e:
            self.fail(f"Descriptor computation failed: {e}")

        # 3. Run Training (Baseline)
        logger.info("Step 3: Running Baseline Training...")
        try:
            from training import main as training_main
            training_main()
            logger.info("Baseline training completed successfully.")
        except Exception as e:
            self.fail(f"Baseline training failed: {e}")

        # 4. Verify Output
        logger.info("Step 4: Verifying output artifacts...")
        baseline_report_path = self.results_dir / "baseline_report.csv"
        
        self.assertTrue(
            baseline_report_path.exists(), 
            f"Baseline report not found at {baseline_report_path}. Pipeline did not produce output."
        )
        
        # Check file size
        self.assertGreater(
            baseline_report_path.stat().st_size, 
            0, 
            "Baseline report is empty."
        )

        # Validate content has MAE
        import pandas as pd
        try:
            df = pd.read_csv(baseline_report_path)
        except Exception as e:
            self.fail(f"Failed to read baseline report CSV: {e}")

        required_columns = ['property', 'model_type', 'MAE']
        for col in required_columns:
            self.assertIn(
                col, df.columns, 
                f"Baseline report missing required column: {col}"
            )

        # Verify at least one numeric MAE value exists (not NaN, not empty string)
        if 'MAE' in df.columns:
            non_null_mae = df['MAE'].dropna()
            self.assertGreater(
                len(non_null_mae), 0, 
                "No valid MAE values found in baseline report."
            )
            # Check if any value is numeric (pandas might read as object if mixed)
            numeric_mae = pd.to_numeric(non_null_mae, errors='coerce').dropna()
            self.assertGreater(
                len(numeric_mae), 0, 
                "No numeric MAE values found in baseline report."
            )

        logger.info(f"Verification passed. Found {len(df)} rows in baseline report.")
        logger.info("Full pipeline MAE output test PASSED.")

    def test_end_to_end_logic(self):
        """
        Legacy placeholder kept for compatibility, now superseded by test_full_pipeline_mae_output.
        """
        logger.info("End-to-end logic test: Structure verified.")
        self.assertTrue(True, "Pipeline structure is valid.")

if __name__ == '__main__':
    unittest.main()