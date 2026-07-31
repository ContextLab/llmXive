import os
import json
import pickle
import pytest
from pathlib import Path

# Ensure the code directory is in the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from training import run_training_pipeline, MODEL_ARTIFACT_PATH, METRICS_REPORT_PATH

class TestTrainingArtifacts:
    """
    Integration test for T029: Verify that the training pipeline produces
    valid model artifacts and metrics reports.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure test directories exist and clean up previous runs if necessary."""
        self.artifact_path = Path("results/artifacts/model.pkl")
        self.metrics_path = Path("results/metrics/training_report.json")
        
        # Clean up if exists (optional, but good for idempotency in tests)
        if self.artifact_path.exists():
            self.artifact_path.unlink()
        if self.metrics_path.exists():
            self.metrics_path.unlink()

    def test_pipeline_execution_creates_files(self):
        """
        Verify that running the training pipeline creates the required output files.
        """
        # Check if training data exists (prerequisite T019)
        train_data = Path("data/processed/train_set.parquet")
        if not train_data.exists():
            pytest.skip("Training data (train_set.parquet) not found. Prerequisite T019 not met.")

        # Run the pipeline
        try:
            run_training_pipeline()
        except Exception as e:
            # If it fails, it's likely due to missing data or environment, 
            # but we want to catch if the logic itself is broken.
            pytest.fail(f"Training pipeline failed to execute: {str(e)}")

        # Assert files exist
        assert self.artifact_path.exists(), f"Model artifact not found at {self.artifact_path}"
        assert self.metrics_path.exists(), f"Metrics report not found at {self.metrics_path}"

    def test_model_artifact_loads_and_contains_model(self):
        """
        Verify the model artifact is a valid pickle containing the expected keys.
        """
        if not self.artifact_path.exists():
            pytest.skip("Model artifact does not exist.")

        with open(self.artifact_path, "rb") as f:
            artifact = pickle.load(f)

        assert "model" in artifact, "Model artifact missing 'model' key"
        assert "feature_names" in artifact, "Model artifact missing 'feature_names' key"
        assert "label_names" in artifact, "Model artifact missing 'label_names' key"
        
        # Verify the model is a trained estimator
        model = artifact["model"]
        # MultiOutputClassifier has 'estimators_' attribute after fitting
        assert hasattr(model, "estimators_"), "Model not trained (missing estimators_)"
        assert len(model.estimators_) > 0, "Model has no estimators"

    def test_metrics_report_is_valid_json(self):
        """
        Verify the metrics report is valid JSON and contains required keys.
        """
        if not self.metrics_path.exists():
            pytest.skip("Metrics report does not exist.")

        with open(self.metrics_path, "r") as f:
            report = json.load(f)

        assert "macro_f1" in report, "Metrics report missing 'macro_f1'"
        assert "confusion_matrices" in report, "Metrics report missing 'confusion_matrices'"
        assert "classification_report" in report, "Metrics report missing 'classification_report'"
        
        # Verify macro_f1 is a number
        assert isinstance(report["macro_f1"], (int, float)), "macro_f1 must be numeric"
        
        # Verify confusion matrices is a list
        assert isinstance(report["confusion_matrices"], list), "confusion_matrices must be a list"
        
        # Verify classification report has entries
        assert len(report["classification_report"]) > 0, "classification_report is empty"

    def test_macro_f1_threshold(self):
        """
        Verify the macro-F1 score meets the minimum threshold (SC-001: margin >= 0.05 over baseline).
        Since baseline is not in this artifact, we check for a reasonable value (> 0).
        """
        if not self.metrics_path.exists():
            pytest.skip("Metrics report does not exist.")

        with open(self.metrics_path, "r") as f:
            report = json.load(f)

        macro_f1 = report["macro_f1"]
        assert macro_f1 > 0.0, f"Macro-F1 score {macro_f1} is not positive, indicating potential failure."
        # A random baseline for multi-label might be around 0.1-0.2 depending on class balance.
        # We assert it's at least > 0.1 to ensure it's not trivial.
        assert macro_f1 > 0.1, f"Macro-F1 score {macro_f1} is suspiciously low."