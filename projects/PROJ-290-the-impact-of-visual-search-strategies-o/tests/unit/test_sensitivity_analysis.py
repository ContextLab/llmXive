"""
Unit tests for Sensitivity Analysis (T025).

These tests verify the logic of loading cluster labels, fitting the descriptive LMM,
and calculating variance across k values. They use mock data to avoid dependency
on the full pipeline execution during unit testing.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import yaml

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis.sensitivity_analysis import (
    load_cluster_labels,
    load_processed_features,
    fit_descriptive_lmm,
    run_sensitivity_analysis,
    save_sensitivity_report
)
from config import get_config

class TestSensitivityAnalysis(unittest.TestCase):

    def setUp(self):
        """Set up temporary directories and mock data for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cfg = get_config()
        # Override paths for testing
        self.cfg["paths"]["processed"] = self.temp_dir.name
        self.cfg["paths"]["results"] = os.path.join(self.temp_dir.name, "results")
        os.makedirs(self.cfg["paths"]["results"], exist_ok=True)

        # Create mock processed features
        self.mock_features = pd.DataFrame({
            "participant_id": [f"p{i}" for i in range(1, 21)],
            "detection_time": np.random.uniform(500, 1500, 20),
            "continuous_ratio": np.random.uniform(0.1, 0.9, 20)
        })
        features_path = os.path.join(self.cfg["paths"]["processed"], "features.csv")
        self.mock_features.to_csv(features_path, index=False)

        # Create mock cluster labels for k=2
        self.mock_labels_k2 = pd.DataFrame({
            "participant_id": [f"p{i}" for i in range(1, 21)],
            "cluster_label_2": np.random.choice([0, 1], 20)
        })
        labels_k2_path = os.path.join(self.cfg["paths"]["processed"], "labels_k2.csv")
        self.mock_labels_k2.to_csv(labels_k2_path, index=False)

        # Create mock cluster labels for k=3
        self.mock_labels_k3 = pd.DataFrame({
            "participant_id": [f"p{i}" for i in range(1, 21)],
            "cluster_label_3": np.random.choice([0, 1, 2], 20)
        })
        labels_k3_path = os.path.join(self.cfg["paths"]["processed"], "labels_k3.csv")
        self.mock_labels_k3.to_csv(labels_k3_path, index=False)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_load_cluster_labels_k2(self):
        """Test loading cluster labels for k=2."""
        df = load_cluster_labels(2, self.cfg)
        self.assertIn("participant_id", df.columns)
        self.assertIn("cluster_label", df.columns)
        self.assertEqual(len(df), 20)

    def test_load_cluster_labels_missing_file(self):
        """Test that loading missing cluster labels raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_cluster_labels(99, self.cfg)

    def test_fit_descriptive_lmm(self):
        """Test fitting the descriptive LMM with mock data."""
        # Merge manually for the test
        merged = self.mock_features.merge(self.mock_labels_k2, on="participant_id")
        merged["cluster_label_2"] = merged["cluster_label_2"].astype("category")
        merged = merged.rename(columns={"cluster_label_2": "cluster_label"})

        result = fit_descriptive_lmm(merged, 2)

        self.assertIn("k", result)
        self.assertEqual(result["k"], 2)
        self.assertIn("coefficients", result)
        self.assertIn("converged", result)
        self.assertIn("cluster_label", str(result["coefficients"])) # Check if cluster label effect is present

    def test_run_sensitivity_analysis_integration(self):
        """Test the full sensitivity analysis pipeline."""
        # This test mocks the statsmodels fitting to ensure it runs without heavy computation
        # and to verify the variance calculation logic.
        with patch('analysis.sensitivity_analysis.MixedLM.from_formula') as mock_fit:
            # Mock the result object
            mock_result = MagicMock()
            mock_result.converged = True
            mock_result.llf = -100.0
            mock_result.aic = 200.0
            mock_result.bic = 210.0
            mock_result.nobs = 20
            mock_result.n_groups = 20
            mock_result.params = {
                "Intercept": 1000.0,
                "C(cluster_label)[T.1]": 50.0
            }
            mock_result.bse = {
                "Intercept": 10.0,
                "C(cluster_label)[T.1]": 5.0
            }
            mock_result.pvalues = {
                "Intercept": 0.001,
                "C(cluster_label)[T.1]": 0.04
            }

            mock_model = MagicMock()
            mock_model.fit.return_value = mock_result
            mock_fit.return_value = mock_model

            report = run_sensitivity_analysis(self.cfg)

            self.assertEqual(report["status"], "completed")
            self.assertIn("summary", report)
            self.assertIn("variance_metrics", report["summary"])
            self.assertIn("cluster_effect_variance", report["summary"]["variance_metrics"])
            self.assertEqual(len(report["model_details"]), 2) # k=2 and k=3

    def test_save_sensitivity_report(self):
        """Test saving the sensitivity report to YAML."""
        report = {
            "task_id": "T025",
            "status": "completed",
            "summary": {
                "variance_metrics": {"cluster_effect_variance": 0.5}
            }
        }
        output_path = save_sensitivity_report(report, self.cfg)

        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r") as f:
            loaded_report = yaml.safe_load(f)
        
        self.assertEqual(loaded_report["task_id"], "T025")
        self.assertEqual(loaded_report["status"], "completed")

if __name__ == "__main__":
    unittest.main()