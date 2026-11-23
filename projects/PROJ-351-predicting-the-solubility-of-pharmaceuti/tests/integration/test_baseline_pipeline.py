"""
Integration test for the full Random Forest baseline pipeline (User Story 1).

This test verifies the end-to-end execution of:
1. Data Download (ESOL)
2. Preprocessing (SMILES -> Graph features)
3. Splitting (Stratified by logS)
4. Baseline Model Training (Random Forest on Morgan Fingerprints)
5. Evaluation (RMSE, R2)
6. Artifact Persistence (Model, Metrics, Logs)

Prerequisites:
- T004 (download_esol.py)
- T005 (preprocess.py)
- T006 (split.py)
- T013 (baseline_rf.py)
"""

import os
import sys
import json
import tempfile
import shutil
import logging
import unittest
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download_esol import fetch_esol_dataset, save_raw_csv
from data.preprocess import load_and_preprocess, main as preprocess_main
from data.split import create_stratified_splits, save_split_indices, main as split_main
from models.baseline_rf import train_random_forest, evaluate_model, save_model, main as rf_main
from setup_logging import setup_logger, log_training_metrics
from config.seeds import ensure_seeded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestBaselinePipelineIntegration(unittest.TestCase):
    """
    Integration test suite for the Random Forest Baseline Pipeline.
    """

    def setUp(self):
        """
        Set up a temporary directory for test artifacts to avoid polluting
        the actual data/ and models/ directories during CI runs.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="esol_test_")
        self.data_dir = Path(self.temp_dir) / "data"
        self.models_dir = Path(self.temp_dir) / "models"
        self.results_dir = Path(self.temp_dir) / "results"
        self.logs_dir = Path(self.temp_dir) / "logs"

        for d in [self.data_dir, self.models_dir, self.results_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Initialize logger for this test run
        self.logger = setup_logger(
            name="test_baseline_integration",
            log_file=str(self.logs_dir / "pipeline_test.log"),
            level=logging.INFO
        )

        # Ensure seeds are set for reproducibility
        ensure_seeded(seed=42)

    def tearDown(self):
        """
        Clean up temporary directory.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _get_paths(self):
        """Helper to get standard paths used by the pipeline scripts."""
        return {
            "raw_csv": self.data_dir / "raw" / "esol_raw.csv",
            "processed_dir": self.data_dir / "processed",
            "split_dir": self.data_dir / "processed",
            "model_path": self.models_dir / "rf_baseline.pkl",
            "metrics_path": self.results_dir / "baseline_metrics.json"
        }

    def test_full_pipeline_execution(self):
        """
        Test the complete pipeline: Download -> Preprocess -> Split -> Train -> Eval.
        """
        paths = self._get_paths()
        paths["raw_csv"].parent.mkdir(parents=True, exist_ok=True)

        # 1. Download Data
        logger.info("Step 1: Fetching ESOL dataset...")
        try:
            df = fetch_esol_dataset()
            save_raw_csv(df, str(paths["raw_csv"]))
            self.assertTrue(paths["raw_csv"].exists(), "Raw CSV not saved")
            self.assertGreater(len(df), 0, "Downloaded dataset is empty")
        except Exception as e:
            self.fail(f"Data download failed: {e}")

        # 2. Preprocess Data
        logger.info("Step 2: Preprocessing data...")
        # We need to call the function directly to avoid CLI argument parsing in tests
        # The main() function in preprocess.py handles the logic
        try:
            # Simulate the main logic of code/data/preprocess.py
            processed_data_path = load_and_preprocess(
                input_file=str(paths["raw_csv"]),
                output_dir=str(paths["processed_dir"]),
                logger=self.logger
            )
            self.assertTrue(processed_data_path.exists(), "Processed data not saved")
            self.assertGreater(processed_data_path.stat().st_size, 0, "Processed file empty")
        except Exception as e:
            self.fail(f"Preprocessing failed: {e}")

        # 3. Split Data
        logger.info("Step 3: Creating stratified splits...")
        try:
            # Simulate the main logic of code/data/split.py
            split_indices_path = create_stratified_splits(
                data_file=str(processed_data_path),
                output_dir=str(paths["split_dir"]),
                logger=self.logger
            )
            self.assertTrue(split_indices_path.exists(), "Split indices not saved")
            with open(split_indices_path, 'r') as f:
                splits = json.load(f)
            self.assertIn("train", splits)
            self.assertIn("val", splits)
            self.assertIn("test", splits)
            self.assertGreater(len(splits["train"]), 0)
        except Exception as e:
            self.fail(f"Splitting failed: {e}")

        # 4. Train Baseline Model
        logger.info("Step 4: Training Random Forest Baseline...")
        try:
            # Simulate the main logic of code/models/baseline_rf.py
            # We call the internal functions to avoid CLI parsing
            processed_file = str(processed_data_path)
            split_file = str(split_indices_path)
            model_path = str(paths["model_path"])
            metrics_path = str(paths["metrics_path"])

            # Load data, train, evaluate, save
            # Note: We assume the functions in baseline_rf.py are exposed as per API surface
            # If they are not, we might need to adapt, but the task says they are.
            
            # Load processed data
            from models.baseline_rf import load_processed_data, prepare_features_and_targets
            train_X, train_y, val_X, val_y, test_X, test_y, feature_names = prepare_features_and_targets(
                processed_file, split_file
            )

            # Train
            model = train_random_forest(train_X, train_y, val_X, val_y)
            
            # Evaluate
            metrics = evaluate_model(model, test_X, test_y)
            
            # Save
            save_model(model, model_path)
            
            # Log metrics
            self.logger.info(f"Baseline Metrics: {metrics}")
            log_training_metrics(
                logger=self.logger,
                metrics=metrics,
                model_path=model_path,
                log_file=str(self.logs_dir / "training_metrics.log")
            )
            
            # Save metrics to JSON for verification
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)

            self.assertTrue(Path(model_path).exists(), "Model not saved")
            self.assertTrue(Path(metrics_path).exists(), "Metrics file not saved")
            
            # Verify metrics structure
            self.assertIn("rmse", metrics)
            self.assertIn("r2", metrics)
            self.assertGreaterEqual(metrics["r2"], -1.0) # R2 can be negative but usually > -1 for this dataset
            self.assertGreater(metrics["rmse"], 0)

        except Exception as e:
            logger.error("Training failed", exc_info=True)
            self.fail(f"Baseline training failed: {e}")

    def test_artifact_integrity(self):
        """
        Verify that all expected artifacts exist and are non-empty after pipeline run.
        """
        # Re-run the pipeline to ensure artifacts exist for this check
        self.test_full_pipeline_execution()
        
        paths = self._get_paths()
        
        # Check Raw Data
        self.assertTrue(paths["raw_csv"].exists())
        self.assertGreater(paths["raw_csv"].stat().st_size, 100) # > 100 bytes

        # Check Processed Data
        processed_file = paths["processed_dir"] / "processed_graphs.json"
        self.assertTrue(processed_file.exists())
        self.assertGreater(processed_file.stat().st_size, 100)

        # Check Splits
        split_file = paths["split_dir"] / "split_indices.json"
        self.assertTrue(split_file.exists())
        
        # Check Model
        self.assertTrue(paths["model_path"].exists())
        self.assertGreater(paths["model_path"].stat().st_size, 100)

        # Check Metrics
        self.assertTrue(paths["metrics_path"].exists())
        with open(paths["metrics_path"], 'r') as f:
            metrics = json.load(f)
        self.assertIn("rmse", metrics)
        self.assertIn("r2", metrics)

        # Check Logs
        log_file = self.logs_dir / "pipeline_test.log"
        self.assertTrue(log_file.exists())
        with open(log_file, 'r') as f:
            log_content = f.read()
        self.assertIn("Baseline Metrics", log_content)


if __name__ == "__main__":
    unittest.main()