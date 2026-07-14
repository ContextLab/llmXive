import os
import json
import tempfile
import unittest
import numpy as np

from models.metrics_writer import write_metrics_json


class TestMetricsWriter(unittest.TestCase):

    def test_write_metrics_json_creates_file(self):
        """Test that write_metrics_json creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_metrics.json")
            metrics = {
                "Linear": {"R2": 0.8, "MAE": 1.0, "RMSE": 1.2},
                "RandomForest": {"R2": 0.9, "MAE": 0.5, "RMSE": 0.7}
            }

            write_metrics_json(metrics, output_path)

            self.assertTrue(os.path.exists(output_path))

    def test_write_metrics_json_content(self):
        """Test that the written JSON contains correct data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_metrics.json")
            metrics = {
                "Linear": {"R2": 0.85, "MAE": 2.0, "RMSE": 2.5},
                "RandomForest": {"R2": 0.92, "MAE": 1.0, "RMSE": 1.5},
                "GradientBoosting": {"R2": 0.95, "MAE": 0.8, "RMSE": 1.1}
            }

            write_metrics_json(metrics, output_path)

            with open(output_path, 'r') as f:
                loaded_metrics = json.load(f)

            self.assertEqual(loaded_metrics["Linear"]["R2"], 0.85)
            self.assertEqual(loaded_metrics["RandomForest"]["MAE"], 1.0)
            self.assertEqual(loaded_metrics["GradientBoosting"]["RMSE"], 1.1)

    def test_write_metrics_json_creates_directory(self):
        """Test that write_metrics_json creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "subdir", "output")
            output_path = os.path.join(nested_dir, "metrics.json")
            metrics = {"Linear": {"R2": 0.5, "MAE": 1.0, "RMSE": 1.0}}

            write_metrics_json(metrics, output_path)

            self.assertTrue(os.path.exists(output_path))

    def test_write_metrics_json_handles_missing_keys(self):
        """Test that missing model keys are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_metrics.json")
            # Missing GradientBoosting
            metrics = {
                "Linear": {"R2": 0.8, "MAE": 1.0, "RMSE": 1.2},
                "RandomForest": {"R2": 0.9, "MAE": 0.5, "RMSE": 0.7}
            }

            # Should not raise
            write_metrics_json(metrics, output_path)

            self.assertTrue(os.path.exists(output_path))
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            self.assertIn("Linear", loaded)
            self.assertIn("RandomForest", loaded)
            # Note: The writer does not auto-add missing models, it just logs a warning.
            # The task requires writing what is provided.

if __name__ == '__main__':
    unittest.main()