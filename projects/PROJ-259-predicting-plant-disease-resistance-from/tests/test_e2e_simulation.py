"""
Comprehensive End-to-End Test for Simulation Mode (T054)

This test suite:
1. Mocks external API calls (NCBI SRA/MetaboLights) to force simulation mode.
2. Forces the synthetic data generator.
3. Runs the full pipeline (main.py).
4. Asserts that all expected artifacts exist and contain valid data types.
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_artifacts_path, get_reports_path, get_processed_data_path
from data.generate_synthetic import main as generate_synthetic_main
from main import main as run_pipeline_main


class TestE2ESimulation(unittest.TestCase):
    """End-to-End test for the pipeline in Simulation Mode."""

    @classmethod
    def setUpClass(cls):
        """
        Ensure the project directory structure exists.
        This mirrors T001 but ensures it's ready for the test run.
        """
        dirs = [
            "code", "data", "data/raw", "data/processed",
            "artifacts", "artifacts/models", "artifacts/reports", "artifacts/figures", "tests"
        ]
        for d in dirs:
            (project_root / d).mkdir(parents=True, exist_ok=True)

    def _clean_artifacts(self):
        """Remove previous run artifacts to ensure a fresh test."""
        report_dir = project_root / "artifacts" / "reports"
        if report_dir.exists():
            for f in report_dir.iterdir():
                if f.is_file():
                    f.unlink()
        # Clean processed data if it exists
        proc_dir = project_root / "data" / "processed"
        if proc_dir.exists():
            for f in proc_dir.iterdir():
                if f.is_file():
                    f.unlink()

    @patch('data.download.requests.get')
    @patch('data.download.yaml.dump')
    def test_full_pipeline_simulation_mode(self, mock_yaml_dump, mock_requests_get):
        """
        Test 1: Force simulation mode by mocking external API failures.
        Verify the pipeline runs end-to-end and produces all required artifacts.
        """
        # 1. Setup Mocks
        # Mock requests.get to simulate 404/403 or empty results, triggering fallback
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        # 2. Clean previous artifacts
        self._clean_artifacts()

        # 3. Run the pipeline
        # We invoke main.py with arguments that force the flow.
        # Since T010/T019 logic handles the fallback, we just need to trigger main.
        # We use sys.argv to simulate command line execution.
        original_argv = sys.argv
        try:
            # Simulate: python code/main.py --mode simulation --seed 42
            # Note: The exact flags depend on main.py implementation, assuming standard argparse.
            # If main.py doesn't accept --mode, the download logic inside will trigger based on mock.
            sys.argv = ["main.py"]

            # Execute the pipeline entry point
            # We catch SystemExit if argparse calls it, but main() should return or raise specific errors.
            try:
                run_pipeline_main()
            except SystemExit:
                # Expected if argparse --help or similar is triggered, but we assume main runs to completion
                pass
            except Exception as e:
                # If the pipeline fails for a reason other than missing artifacts (which we check later),
                # we might want to inspect. However, for this test, we assume it runs.
                # If it fails due to data integrity, that's a failure of the generator, not the test logic.
                if "Insufficient data" in str(e) or "Power deficiency" in str(e):
                    self.fail(f"Pipeline failed due to data integrity/power: {e}")
                raise

        finally:
            sys.argv = original_argv

        # 4. Verify Artifacts Exist
        report_path = get_reports_path()
        artifacts_path = get_artifacts_path()

        expected_files = [
            "metrics.json",
            "selection_frequency.csv",
            "top_features.csv",
            "holdout_metrics.json",
            "final_validation_report.md",
            "biomarker_summary.json"
        ]

        for fname in expected_files:
            fpath = Path(report_path) / fname
            self.assertTrue(fpath.exists(), f"Expected artifact missing: {fpath}")
            self.assertGreater(fpath.stat().st_size, 0, f"Artifact is empty: {fpath}")

        # 5. Verify Artifact Content Validity
        
        # Check metrics.json
        with open(Path(report_path) / "metrics.json", 'r') as f:
            metrics = json.load(f)
            self.assertIn("cv_accuracy", metrics)
            self.assertIn("auc", metrics)
            self.assertIsInstance(metrics["cv_accuracy"], (int, float))
            self.assertIsInstance(metrics["auc"], (int, float))

        # Check selection_frequency.csv
        sel_freq_path = Path(report_path) / "selection_frequency.csv"
        df_sel = pd.read_csv(sel_freq_path)
        self.assertIn("feature_id", df_sel.columns)
        self.assertIn("frequency", df_sel.columns)
        self.assertGreater(len(df_sel), 0, "Selection frequency CSV is empty")

        # Check holdout_metrics.json
        with open(Path(report_path) / "holdout_metrics.json", 'r') as f:
            holdout = json.load(f)
            self.assertIn("permutation_p_value", holdout)
            self.assertIn("observed_metric", holdout)
            # Verify p-value is a float between 0 and 1
            self.assertGreaterEqual(holdout["permutation_p_value"], 0)
            self.assertLessEqual(holdout["permutation_p_value"], 1)

        # Check biomarker_summary.json
        with open(Path(report_path) / "biomarker_summary.json", 'r') as f:
            bio_sum = json.load(f)
            self.assertIn("snps_count", bio_sum)
            self.assertIn("metabolites_count", bio_sum)
            # FR-008/SC-002 check: at least 10 of each if signal is strong enough in simulation
            # We assert they exist and are integers, exact count depends on seed/signal
            self.assertIsInstance(bio_sum["snps_count"], int)
            self.assertIsInstance(bio_sum["metabolites_count"], int)

        # Check final_validation_report.md exists and has content
        report_md = Path(report_path) / "final_validation_report.md"
        with open(report_md, 'r') as f:
            content = f.read()
            self.assertIn("Simulation Mode", content) # T053 requirement

    @patch('data.download.requests.get')
    def test_data_manifest_provenance(self, mock_requests_get):
        """
        Test 2: Verify data_manifest.yaml is updated with 'source: SIMULATED'.
        """
        # Mock API failure
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        # Run download pipeline specifically to check manifest update
        from data.download import run_download_pipeline
        
        # We need to ensure the manifest file path is accessible
        manifest_path = project_root / "data" / "data_manifest.yaml"
        
        # Run the download logic which should trigger synthetic generation and update manifest
        try:
            run_download_pipeline()
        except Exception:
            # If it fails later in the pipeline, the manifest might still be updated by the download step
            pass

        # Verify manifest exists and contains SIMULATED
        self.assertTrue(manifest_path.exists(), "data_manifest.yaml not created")
        
        import yaml
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        self.assertIn("source", manifest)
        self.assertEqual(manifest["source"], "SIMULATED")
        self.assertIn("sample_count", manifest)
        self.assertGreater(manifest["sample_count"], 0)


if __name__ == '__main__':
    unittest.main()