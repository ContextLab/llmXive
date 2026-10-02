"""
Integration tests for the modeling pipeline.
Verifies that the best model loads correctly and performs predictions on held-out data.
"""
import os
import sys
import json
import pickle
import tempfile
import pytest
from pathlib import Path

# Ensure code is in path for imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.modeling.train import load_clean_data, prepare_features_targets, train_model
from src.modeling.metrics import load_best_model, collect_all_metrics
from src.utils.logging import get_modeling_logger

logger = get_modeling_logger()

# Constants for test paths relative to project root
PROJECT_ROOT = code_root.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
CLEAN_DATA_PATH = DATA_DIR / "mgb2_clean.csv"
BEST_MODEL_PATH = DATA_DIR / "best_model.pkl"
METRICS_PATH = DATA_DIR / "model_metrics.json"


@pytest.fixture(scope="module")
def model_and_data():
    """
    Fixture to load the trained model and clean data for integration tests.
    Skips if artifacts are missing (simulating a clean run where data isn't ready).
    """
    if not CLEAN_DATA_PATH.exists():
        pytest.skip(f"Clean data file not found at {CLEAN_DATA_PATH}. Run preprocessing first.")
    
    if not BEST_MODEL_PATH.exists():
        pytest.skip(f"Best model file not found at {BEST_MODEL_PATH}. Run training first.")

    # Load model
    with open(BEST_MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    # Load and prepare data
    df = load_clean_data(CLEAN_DATA_PATH)
    X, y, _ = prepare_features_targets(df)

    # Split into train/test to simulate held-out data
    # Using a simple split since we just need to verify prediction capability
    split_idx = int(len(X) * 0.8)
    X_test = X[split_idx:]
    y_test = y[split_idx:]

    if len(X_test) == 0:
        pytest.skip("Dataset too small for held-out test split.")

    return model, X_test, y_test


class TestModelingIntegration:
    """
    Integration tests for the modeling pipeline (US2).
    """

    def test_best_model_loads(self, model_and_data):
        """
        Verify that the best_model.pkl file can be loaded without errors
        and is a valid scikit-learn estimator.
        """
        model, _, _ = model_and_data
        
        assert model is not None, "Model loaded is None"
        assert hasattr(model, 'predict'), "Loaded object does not have a 'predict' method"
        assert hasattr(model, 'score'), "Loaded object does not have a 'score' method"
        logger.info("Model loaded successfully and has expected attributes.")

    def test_model_predicts_on_held_out_data(self, model_and_data):
        """
        Verify that the loaded model can successfully predict on held-out data
        and returns the expected shape of predictions.
        """
        model, X_test, y_test = model_and_data
        
        # Perform prediction
        predictions = model.predict(X_test)
        
        # Verify shape
        assert predictions.shape[0] == y_test.shape[0], \
            f"Prediction count {predictions.shape[0]} does not match test set size {y_test.shape[0]}"
        
        # Verify no NaNs in predictions (unless model is fundamentally broken)
        import numpy as np
        assert not np.any(np.isnan(predictions)), "Predictions contain NaN values"
        
        logger.info(f"Predictions generated successfully: {len(predictions)} values.")

    def test_model_scores_on_held_out_data(self, model_and_data):
        """
        Verify that the model can calculate a score (R^2) on held-out data.
        The score should be a float.
        """
        model, X_test, y_test = model_and_data
        
        score = model.score(X_test, y_test)
        
        assert isinstance(score, float), f"Score is not a float, got {type(score)}"
        # R^2 can be negative, but usually > -1 for reasonable models
        assert score > -100, f"Model score {score} is unreasonably low"
        
        logger.info(f"Model R^2 score on held-out data: {score:.4f}")

    def test_metrics_file_exists_and_valid(self):
        """
        Verify that the model_metrics.json file exists and contains expected keys.
        """
        if not METRICS_PATH.exists():
            pytest.skip(f"Metrics file not found at {METRICS_PATH}. Run training first.")

        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)

        assert isinstance(metrics, dict), "Metrics file content is not a JSON object"
        assert "best_model_name" in metrics, "Missing 'best_model_name' in metrics"
        assert "best_model_score" in metrics, "Missing 'best_model_score' in metrics"
        
        # Check that all models are listed
        assert "models" in metrics, "Missing 'models' list in metrics"
        assert len(metrics["models"]) > 0, "No models recorded in metrics"

        logger.info("Metrics file is valid and contains expected data.")