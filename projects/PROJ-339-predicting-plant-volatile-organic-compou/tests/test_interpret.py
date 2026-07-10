"""
Contract tests for interpretation output schema (User Story 3).

These tests validate that the output artifacts from code/04_interpret.py
conform to the expected schema defined in the project specifications.

Dependencies:
  - data/models/random_forest.pkl (produced by T024)
  - data/processed/merged_dataset.csv (produced by T017)
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Define expected output paths based on tasks.md
INTERPRETATION_REPORT_PATH = project_root / "data" / "results" / "interpretation_report.json"
FEATURE_IMPORTANCE_PATH = project_root / "data" / "results" / "feature_importance_pvalues.json"
STABILITY_METRICS_PATH = project_root / "data" / "results" / "stability_metrics.json"
SHAP_SUMMARY_PATH = project_root / "data" / "results" / "shap_summary.png"
MODEL_PATH = project_root / "data" / "models" / "random_forest.pkl"
MERGED_DATA_PATH = project_root / "data" / "processed" / "merged_dataset.csv"


class TestInterpretationSchema(unittest.TestCase):
    """
    Contract tests for the interpretation pipeline outputs.
    Ensures that the generated files match the required schema.
    """

    @classmethod
    def setUpClass(cls):
        """
        Verify that prerequisite artifacts exist before running tests.
        If prerequisites are missing, the test suite is skipped.
        """
        cls.prerequisites_missing = False
        missing_files = []

        if not MODEL_PATH.exists():
            missing_files.append(str(MODEL_PATH))
        if not MERGED_DATA_PATH.exists():
            missing_files.append(str(MERGED_DATA_PATH))

        if missing_files:
            cls.prerequisites_missing = True
            print(f"⚠ Skipping tests: Missing prerequisites: {missing_files}")

    def test_01_interpretation_report_schema(self):
        """
        Contract Test: Verify data/results/interpretation_report.json schema.
        
        Expected schema:
        {
          "disclaimer": str,
          "fdr_threshold": float,
          "top_features": [
            {"feature": str, "importance": float, "p_value": float, "fdr_corrected": float},
            ...
          ],
          "overlap_statistics": {
            "terpene_synthase_overlap": float,
            "total_features": int,
            "tps_features": int
          },
          "methodology": str
        }
        """
        if self.prerequisites_missing:
            self.skipTest("Prerequisites missing")

        self.assertTrue(INTERPRETATION_REPORT_PATH.exists(), 
                        f"File not found: {INTERPRETATION_REPORT_PATH}")

        with open(INTERPRETATION_REPORT_PATH, 'r') as f:
            report = json.load(f)

        # Top-level keys
        self.assertIn("disclaimer", report)
        self.assertIn("fdr_threshold", report)
        self.assertIn("top_features", report)
        self.assertIn("overlap_statistics", report)
        self.assertIn("methodology", report)

        # Type checks
        self.assertIsInstance(report["disclaimer"], str)
        self.assertIsInstance(report["fdr_threshold"], (int, float))
        self.assertIsInstance(report["top_features"], list)
        self.assertIsInstance(report["overlap_statistics"], dict)
        self.assertIsInstance(report["methodology"], str)

        # Content checks
        self.assertGreater(len(report["disclaimer"]), 10, "Disclaimer too short")
        self.assertIn("associational", report["disclaimer"].lower(), 
                      "Disclaimer missing associational warning")

        # Check top_features structure
        self.assertGreater(len(report["top_features"]), 0, "No features reported")
        for feat in report["top_features"]:
            self.assertIn("feature", feat)
            self.assertIn("importance", feat)
            self.assertIn("p_value", feat)
            self.assertIn("fdr_corrected", feat)
            self.assertIsInstance(feat["feature"], str)
            self.assertIsInstance(feat["importance"], (int, float))
            self.assertIsInstance(feat["p_value"], (int, float))
            self.assertIsInstance(feat["fdr_corrected"], (int, float))

        # Check overlap_statistics structure
        overlap = report["overlap_statistics"]
        self.assertIn("terpene_synthase_overlap", overlap)
        self.assertIn("total_features", overlap)
        self.assertIn("tps_features", overlap)
        self.assertIsInstance(overlap["total_features"], int)
        self.assertIsInstance(overlap["tps_features"], int)

    def test_02_feature_importance_pvalues_schema(self):
        """
        Contract Test: Verify data/results/feature_importance_pvalues.json schema.
        
        Expected schema:
        {
          "method": str,
          "correction_method": str,
          "features": {
            "feature_name": {
              "raw_p_value": float,
              "fdr_corrected_p_value": float,
              "significant": bool
            },
            ...
          }
        }
        """
        if self.prerequisites_missing:
            self.skipTest("Prerequisites missing")

        self.assertTrue(FEATURE_IMPORTANCE_PATH.exists(), 
                        f"File not found: {FEATURE_IMPORTANCE_PATH}")

        with open(FEATURE_IMPORTANCE_PATH, 'r') as f:
            data = json.load(f)

        self.assertIn("method", data)
        self.assertIn("correction_method", data)
        self.assertIn("features", data)

        self.assertEqual(data["correction_method"], "benjamini-hochberg", 
                         "Expected Benjamini-Hochberg correction")

        self.assertIsInstance(data["features"], dict)
        self.assertGreater(len(data["features"]), 0, "No features in p-value file")

        for feat_name, feat_data in data["features"].items():
            self.assertIn("raw_p_value", feat_data)
            self.assertIn("fdr_corrected_p_value", feat_data)
            self.assertIn("significant", feat_data)
            self.assertIsInstance(feat_data["raw_p_value"], (int, float))
            self.assertIsInstance(feat_data["fdr_corrected_p_value"], (int, float))
            self.assertIsInstance(feat_data["significant"], bool)

    def test_03_stability_metrics_schema(self):
        """
        Contract Test: Verify data/results/stability_metrics.json schema.
        
        Expected schema:
        {
          "metric": str,
          "feature_rank_stability": {
            "feature_name": {
              "mean_rank": float,
              "std_rank": float,
              "cv": float
            },
            ...
          },
          "overall_stability_score": float
        }
        """
        if self.prerequisites_missing:
            self.skipTest("Prerequisites missing")

        self.assertTrue(STABILITY_METRICS_PATH.exists(), 
                        f"File not found: {STABILITY_METRICS_PATH}")

        with open(STABILITY_METRICS_PATH, 'r') as f:
            data = json.load(f)

        self.assertIn("metric", data)
        self.assertIn("feature_rank_stability", data)
        self.assertIn("overall_stability_score", data)

        self.assertIsInstance(data["feature_rank_stability"], dict)
        self.assertIsInstance(data["overall_stability_score"], (int, float))
        self.assertGreaterEqual(data["overall_stability_score"], 0.0)
        self.assertLessEqual(data["overall_stability_score"], 1.0)

        for feat_name, metrics in data["feature_rank_stability"].items():
            self.assertIn("mean_rank", metrics)
            self.assertIn("std_rank", metrics)
            self.assertIn("cv", metrics)
            self.assertIsInstance(metrics["mean_rank"], (int, float))
            self.assertIsInstance(metrics["std_rank"], (int, float))
            self.assertIsInstance(metrics["cv"], (int, float))

    def test_04_shap_summary_exists(self):
        """
        Contract Test: Verify that the SHAP summary plot file exists.
        """
        if self.prerequisites_missing:
            self.skipTest("Prerequisites missing")

        self.assertTrue(SHAP_SUMMARY_PATH.exists(), 
                        f"SHAP summary plot not found: {SHAP_SUMMARY_PATH}")
        
        # Basic check that file is not empty
        self.assertGreater(SHAP_SUMMARY_PATH.stat().st_size, 0, 
                           "SHAP summary plot file is empty")


if __name__ == "__main__":
    unittest.main()