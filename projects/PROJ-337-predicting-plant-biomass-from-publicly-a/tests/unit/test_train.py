"""
Unit tests for the Random Forest training module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.models.train import (
    load_training_data,
    compute_metrics,
    train_random_forest_cv
)


class TestComputeMetrics(unittest.TestCase):
    """Tests for the compute_metrics function."""

    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])

        metrics = compute_metrics(y_true, y_pred)

        # Check that all required keys are present
        self.assertIn("rmse", metrics)
        self.assertIn("mae", metrics)
        self.assertIn("r2", metrics)

        # Check that values are floats
        self.assertIsInstance(metrics["rmse"], float)
        self.assertIsInstance(metrics["mae"], float)
        self.assertIsInstance(metrics["r2"], float)

        # Check that R² is between 0 and 1 for this reasonable prediction
        self.assertLessEqual(metrics["r2"], 1.0)
        self.assertGreater(metrics["r2"], 0.0)

    def test_perfect_prediction(self):
        """Test metrics for perfect prediction."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        metrics = compute_metrics(y_true, y_pred)

        self.assertEqual(metrics["rmse"], 0.0)
        self.assertEqual(metrics["mae"], 0.0)
        self.assertEqual(metrics["r2"], 1.0)


class TestLoadTrainingData(unittest.TestCase):
    """Tests for the load_training_data function."""

    def setUp(self):
        """Create a temporary CSV file for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_csv = Path(self.temp_dir.name) / "test_data.csv"

        # Create test data
        data = {
            "site_id": [1, 2, 3, 4],
            "band_1": [0.1, 0.2, 0.3, 0.4],
            "band_2": [0.5, 0.6, 0.7, 0.8],
            "biomass_kg_per_m2": [10.0, 20.0, 30.0, 40.0],
            "cloud_flag": [0, 0, 1, 0]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_csv, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_load_data(self):
        """Test loading data from CSV."""
        X, y, feature_names = load_training_data(str(self.test_csv))

        # Check shapes
        self.assertEqual(X.shape[0], 4)
        self.assertEqual(X.shape[1], 2)  # band_1 and band_2
        self.assertEqual(len(y), 4)

        # Check feature names
        self.assertIn("band_1", feature_names)
        self.assertIn("band_2", feature_names)
        self.assertNotIn("biomass_kg_per_m2", feature_names)
        self.assertNotIn("cloud_flag", feature_names)

    def test_missing_target_column(self):
        """Test error handling for missing target column."""
        data = {
            "site_id": [1, 2, 3],
            "band_1": [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        bad_csv = Path(self.temp_dir.name) / "bad_data.csv"
        df.to_csv(bad_csv, index=False)

        with self.assertRaises(ValueError):
            load_training_data(str(bad_csv))


class TestTrainRandomForestCV(unittest.TestCase):
    """Tests for the train_random_forest_cv function."""

    def test_training_runs(self):
        """Test that training completes without errors."""
        # Generate synthetic data for testing
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"

            results = train_random_forest_cv(
                X=X,
                y=y,
                n_splits=3,  # Use 3 folds for faster testing
                n_estimators=5,  # Small number for speed
                output_path=str(output_path)
            )

            # Check structure
            self.assertEqual(results["model_type"], "RandomForest")
            self.assertEqual(results["n_splits"], 3)
            self.assertIn("fold_metrics", results)
            self.assertIn("aggregate_metrics", results)

            # Check fold metrics
            self.assertEqual(len(results["fold_metrics"]), 3)
            for fold in results["fold_metrics"]:
                self.assertIn("fold", fold)
                self.assertIn("rmse", fold)
                self.assertIn("mae", fold)
                self.assertIn("r2", fold)

            # Check aggregate metrics
            agg = results["aggregate_metrics"]
            self.assertIn("rmse_mean", agg)
            self.assertIn("r2_mean", agg)

            # Check file was saved
            self.assertTrue(output_path.exists())
            with open(output_path) as f:
                saved_data = json.load(f)
            self.assertEqual(saved_data["model_type"], "RandomForest")

    def test_execution_time_tracked(self):
        """Test that execution time is recorded."""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = np.random.randn(50)

        results = train_random_forest_cv(
            X=X,
            y=y,
            n_splits=2,
            n_estimators=2
        )

        self.assertIn("execution_time_seconds", results)
        self.assertGreater(results["execution_time_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
