import pytest
import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.heuristics.conflict_detector import ConflictDetector

@pytest.fixture
def synthetic_data(tmp_path):
    """Creates a temporary synthetic dataset for testing."""
    data = [
        {
            "patch_a": "The system is running on port 8080.",
            "patch_b": "The system is running on port 8080.",
            "is_contradiction": False
        },
        {
            "patch_a": "The system is running on port 8080.",
            "patch_b": "The system has been shut down.",
            "is_contradiction": True
        },
        {
            "patch_a": "User 'admin' has root access.",
            "patch_b": "User 'admin' has root access.",
            "is_contradiction": False
        },
        {
            "patch_a": "User 'admin' has root access.",
            "patch_b": "User 'admin' has been revoked.",
            "is_contradiction": True
        }
    ]
    file_path = tmp_path / "synthetic_pairs.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return str(file_path)

@pytest.fixture
def output_dir(tmp_path):
    return str(tmp_path / "output")

class TestConflictDetectorModelSensitivity:
    """
    Tests for T014b: Model size sensitivity analysis execution logic.
    """

    def test_detector_initialization(self):
        """Test that the detector initializes correctly with a small model."""
        detector = ConflictDetector(model_name="distilbert-base-uncased", seed=42)
        assert detector.model_name == "distilbert-base-uncased"
        assert detector.threshold == 0.90

    def test_run_sensitivity_analysis_models_creates_file(self, synthetic_data, output_dir):
        """
        Verify that run_sensitivity_analysis_models creates the output CSV
        and contains the expected columns for the specified models.
        """
        detector = ConflictDetector(seed=42)
        output_path = os.path.join(output_dir, "sensitivity_analysis_models.csv")

        # Run the analysis with a small subset of models and thresholds
        # Using only 'distilbert-base-uncased' to keep test execution time low
        # but verifying the logic works for the list input
        detector.run_sensitivity_analysis_models(
            model_names=["distilbert-base-uncased"],
            data_path=synthetic_data,
            thresholds=[0.9, 0.95],
            output_path=output_path
        )

        assert os.path.exists(output_path), "Output CSV file was not created."

        with open(output_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0, "CSV file is empty."
        assert "model_name" in reader.fieldnames
        assert "threshold" in reader.fieldnames
        assert "precision" in reader.fieldnames
        assert "recall" in reader.fieldnames
        assert "f1" in reader.fieldnames

    def test_multiple_models_execution(self, synthetic_data, output_dir):
        """
        Test execution logic with multiple models (simulated by running twice).
        Ensures the function handles the list of models correctly.
        """
        detector = ConflictDetector(seed=42)
        output_path = os.path.join(output_dir, "multi_model_analysis.csv")

        # We use the same model twice here to simulate the list processing
        # without actually downloading a second large model in the test environment
        # In production, this would be ["distilbert-base-uncased", "bert-base-uncased"]
        detector.run_sensitivity_analysis_models(
            model_names=["distilbert-base-uncased", "distilbert-base-uncased"],
            data_path=synthetic_data,
            thresholds=[0.9],
            output_path=output_path
        )

        with open(output_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 2 rows (one for each model entry in the list)
        assert len(rows) == 2, "Expected 2 rows for 2 model entries."

    def test_error_handling_graceful_continue(self, synthetic_data, output_dir):
        """
        Test that if a model fails to load, the function logs the error
        and continues to the next model instead of crashing the whole run.
        """
        detector = ConflictDetector(seed=42)
        output_path = os.path.join(output_dir, "error_handling.csv")

        # Include a non-existent model to trigger an error
        detector.run_sensitivity_analysis_models(
            model_names=["non-existent-model-xyz", "distilbert-base-uncased"],
            data_path=synthetic_data,
            thresholds=[0.9],
            output_path=output_path
        )

        # The file should still be created and contain results for the valid model
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should contain 1 row (for the valid model)
        assert len(rows) == 1
        assert rows[0]['model_name'] == 'distilbert-base-uncased'