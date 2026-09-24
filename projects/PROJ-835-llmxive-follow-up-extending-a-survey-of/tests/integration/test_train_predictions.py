import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.models.train import save_predictions, save_model_artifact, evaluate_model
from sklearn.linear_model import LogisticRegression

class TestTrainPredictions:
    """
    Integration tests for T024: Save trained model artifact and prediction probabilities.
    """

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test outputs."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_save_predictions_csv_structure(self, temp_data_dir):
        """Verify that save_predictions creates a valid CSV with correct columns."""
        # Prepare mock data
        y_true = np.array([0, 1, 0, 1, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        y_prob = np.array([[0.9, 0.1], [0.1, 0.9], [0.8, 0.2], [0.3, 0.7], [0.2, 0.8]])
        anomaly_scores = np.array([1.2, 5.4, 2.1, 6.7, 3.3])

        output_path = save_predictions(
            y_true, y_pred, y_prob, anomaly_scores, temp_data_dir, "test_predictions.csv"
        )

        # Verify file exists
        assert os.path.exists(output_path), "predictions.csv file was not created"

        # Verify CSV content
        df = pd.read_csv(output_path)
        expected_columns = ["true_label", "predicted_label", "predicted_prob_jailbreak", "anomaly_score"]
        assert list(df.columns) == expected_columns, f"Columns mismatch: {list(df.columns)}"

        assert len(df) == 5, "Row count mismatch"
        assert df['true_label'].dtype in [np.int64, int], "true_label should be integer"
        assert df['predicted_prob_jailbreak'].dtype in [np.float64, float], "probabilities should be float"

    def test_save_model_artifact_schema(self, temp_data_dir):
        """Verify that save_model_artifact creates a valid JSON with required keys."""
        # Create a mock model
        model = LogisticRegression()
        X_train = np.random.rand(10, 5)
        y_train = np.random.randint(0, 2, 10)
        model.fit(X_train, y_train)

        metrics = {
            "accuracy": 0.85,
            "precision": 0.80,
            "recall": 0.90,
            "f1_score": 0.85,
            "confusion_matrix": [[8, 2], [1, 9]]
        }

        benign_stats = {
            "mean": np.array([0.5, 0.5, 0.5, 0.5, 0.5]),
            "covariance": np.eye(5),
            "n_samples": 10
        }

        output_path = save_model_artifact(
            model, metrics, benign_stats, temp_data_dir, "test_model.json"
        )

        assert os.path.exists(output_path), "model_artifact.json file was not created"

        with open(output_path, 'r') as f:
            artifact = json.load(f)

        # Verify schema
        assert "model_type" in artifact
        assert artifact["model_type"] == "LogisticRegression"
        assert "coefficients" in artifact
        assert "intercept" in artifact
        assert "metrics" in artifact
        assert "benign_statistics" in artifact
        assert "mean" in artifact["benign_statistics"]
        assert "covariance" in artifact["benign_statistics"]
        assert "n_samples" in artifact["benign_statistics"]

    def test_predictions_file_path_convention(self, temp_data_dir):
        """Verify that predictions are saved to the correct path relative to output_dir."""
        y_true = np.array([0, 1])
        y_pred = np.array([0, 1])
        y_prob = np.array([[0.9, 0.1], [0.1, 0.9]])
        anomaly_scores = np.array([1.0, 2.0])

        # Save with specific filename
        result_path = save_predictions(
            y_true, y_pred, y_prob, anomaly_scores, temp_data_dir, "predictions.csv"
        )

        expected_path = os.path.join(temp_data_dir, "predictions.csv")
        assert result_path == expected_path, f"Path mismatch: {result_path} vs {expected_path}"
        assert os.path.exists(expected_path), "File not found at expected path"
        
        # Verify content is real (not empty)
        df = pd.read_csv(expected_path)
        assert not df.empty, "predictions.csv is empty"