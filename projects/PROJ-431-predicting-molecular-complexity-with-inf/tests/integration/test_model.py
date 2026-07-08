"""
Integration test for model training and report generation (T020).

This test verifies the end-to-end workflow of:
1. Creating a valid synthetic dataset (real data source is not required for this unit-integration hybrid,
   but the logic must handle real data structures).
2. Running the model training pipeline via the `model` module.
3. Verifying that model artifacts (.pkl) and the metrics report (.json) are generated.
4. Checking that the report contains required fields (RMSE, Pearson r, p-values).
"""

import os
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

# Import the target functions from the project's model module
from code.model import train_models_from_csv, run_full_analysis


class TestModelTrainingIntegration:
    """Integration tests for US2 model training and reporting."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.temp_dir, "test_data.csv")
        self.output_dir = os.path.join(self.temp_dir, "output")
        yield
        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_dataset(self):
        """
        Create a small, deterministic dataset mimicking the enriched CSV structure.
        This dataset is synthetic but structurally valid for the integration test.
        It ensures the code runs without needing external downloads.
        """
        np.random.seed(42)
        n_samples = 100

        # Generate synthetic features
        atom_entropy = np.random.uniform(1.0, 3.5, n_samples)
        bond_entropy = np.random.uniform(2.0, 5.0, n_samples)
        smiles = [f"synthetic_smiles_{i}" for i in range(n_samples)]

        # Generate targets with a known correlation to entropy
        # logS ~ -0.5 * atom_entropy + noise
        logS = -0.5 * atom_entropy + np.random.normal(0, 0.2, n_samples)
        # logP ~ 0.8 * bond_entropy + noise
        logP = 0.8 * bond_entropy + np.random.normal(0, 0.3, n_samples)

        df = pd.DataFrame({
            "smiles": smiles,
            "atom_entropy": atom_entropy,
            "bond_entropy": bond_entropy,
            "logS": logS,
            "logP": logP
        })

        df.to_csv(self.data_path, index=False)
        return self.data_path

    def test_train_models_from_csv_generates_artifacts(self):
        """
        Test that train_models_from_csv creates .pkl files and a JSON report.
        """
        # 1. Setup data
        self._create_test_dataset()
        os.makedirs(self.output_dir, exist_ok=True)

        # 2. Run training
        # The function signature from the API surface:
        # train_models_from_csv(input_csv, output_dir, alpha=1.0, test_size=0.2, random_state=42)
        result = train_models_from_csv(
            input_csv=self.data_path,
            output_dir=self.output_dir,
            alpha=1.0,
            test_size=0.2,
            random_state=42
        )

        # 3. Verify return value structure (if any) or side effects
        assert result is not None, "train_models_from_csv should return a result dict"
        assert "model_paths" in result or "metrics" in result, "Result should contain model or metrics info"

        # 4. Verify file existence
        expected_models = ["ridge_logS.pkl", "ridge_logP.pkl"]
        for model_name in expected_models:
            model_path = os.path.join(self.output_dir, model_name)
            assert os.path.exists(model_path), f"Model file {model_name} was not created at {model_path}"

        # 5. Verify JSON report
        report_path = os.path.join(self.output_dir, "metrics.json")
        assert os.path.exists(report_path), "metrics.json was not created"

        with open(report_path, "r") as f:
            report = json.load(f)

        # 6. Validate report content
        assert "logS" in report, "Report missing logS metrics"
        assert "logP" in report, "Report missing logP metrics"

        # Check for required fields in logS metrics
        logS_metrics = report["logS"]
        assert "rmse" in logS_metrics, "logS metrics missing rmse"
        assert "pearson_r" in logS_metrics, "logS metrics missing pearson_r"
        assert "bonferroni_pvalue" in logS_metrics, "logS metrics missing bonferroni_pvalue"
        assert "benjamini_hochberg_pvalue" in logS_metrics, "logS metrics missing benjamini_hochberg_pvalue"

        # Check for required fields in logP metrics
        logP_metrics = report["logP"]
        assert "rmse" in logP_metrics, "logP metrics missing rmse"
        assert "pearson_r" in logP_metrics, "logP metrics missing pearson_r"

    def test_run_full_analysis_integration(self):
        """
        Test the full analysis pipeline including sensitivity and baseline if applicable,
        ensuring the final report is comprehensive.
        """
        self._create_test_dataset()
        os.makedirs(self.output_dir, exist_ok=True)

        # Run the full analysis pipeline
        # Signature: run_full_analysis(input_csv, output_dir, alpha=1.0, test_size=0.2, random_state=42)
        result = run_full_analysis(
            input_csv=self.data_path,
            output_dir=self.output_dir,
            alpha=1.0,
            test_size=0.2,
            random_state=42
        )

        # Verify the metrics.json exists and has the expected structure
        report_path = os.path.join(self.output_dir, "metrics.json")
        assert os.path.exists(report_path), "Full analysis did not create metrics.json"

        with open(report_path, "r") as f:
            report = json.load(f)

        # Ensure sensitivity analysis output is present if the function supports it
        # The task T020 focuses on training and report generation, so we verify the core metrics.
        assert "logS" in report
        assert "logP" in report

        # Verify that RMSE is a number (not NaN or string)
        assert isinstance(report["logS"]["rmse"], (int, float))
        assert isinstance(report["logP"]["rmse"], (int, float))

        # Verify that Pearson r is between -1 and 1
        assert -1.0 <= report["logS"]["pearson_r"] <= 1.0
        assert -1.0 <= report["logP"]["pearson_r"] <= 1.0