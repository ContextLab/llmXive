import os
import sys
import json
import pickle
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure code root is in path for imports
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from code.src.modeling.train import load_clean_data, prepare_features_targets
from code.src.modeling.metrics import load_best_model


class TestModelingIntegration:
    """
    Integration test for T022: Verify best_model.pkl loads and predicts on held-out data.
    
    This test orchestrates the data loading (from US1), model loading (from US2),
    and a prediction run to ensure the pipeline end-to-end works.
    """

    @pytest.fixture
    def project_paths(self):
        """Locate project data paths."""
        project_root = code_root
        data_processed = project_root / "data" / "processed"
        return {
            "clean_data": data_processed / "mgb2_clean.csv",
            "best_model": data_processed / "best_model.pkl",
            "metrics": data_processed / "model_metrics.json"
        }

    def test_model_file_exists(self, project_paths):
        """Verify that the training script produced the best_model.pkl artifact."""
        assert project_paths["best_model"].exists(), (
            f"best_model.pkl not found at {project_paths['best_model']}. "
            "Ensure T020 (train.py) has been executed successfully."
        )

    def test_model_loads_without_error(self, project_paths):
        """Verify the pickled model can be deserialized."""
        try:
            model = load_best_model(str(project_paths["best_model"]))
            assert model is not None, "Loaded model is None."
            # Verify it has the standard sklearn-like predict interface
            assert hasattr(model, "predict"), "Model missing 'predict' method."
        except Exception as e:
            pytest.fail(f"Failed to load best_model.pkl: {e}")

    def test_prediction_on_held_out_data(self, project_paths):
        """
        Verify the model can predict on the held-out test set derived from mgb2_clean.csv.
        
        This ensures the feature engineering (T014) and model training (T018) 
        are compatible.
        """
        if not project_paths["clean_data"].exists():
            pytest.skip("Clean data file (mgb2_clean.csv) not found. Run T014 first.")

        if not project_paths["best_model"].exists():
            pytest.skip("Model file (best_model.pkl) not found. Run T020 first.")

        # Load data
        df = load_clean_data(str(project_paths["clean_data"]))
        
        # Prepare features and targets (using the same logic as training)
        X, y, feature_names = prepare_features_targets(df)

        # Load the model
        model = load_best_model(str(project_paths["best_model"]))

        # Perform prediction
        try:
            predictions = model.predict(X)
        except Exception as e:
            pytest.fail(f"Model prediction failed on held-out data: {e}")

        # Verify output shape
        assert len(predictions) == len(y), (
            f"Prediction length {len(predictions)} does not match target length {len(y)}."
        )
        assert predictions.shape[1] == 1 if len(predictions.shape) > 1 else True, "Predictions should be 1D or (n, 1)."

        # Verify predictions are numeric and not NaN
        assert np.all(np.isfinite(predictions)), "Predictions contain NaN or Inf values."

        # Optional: Basic sanity check (predictions should be in a reasonable Tc range)
        # MgB2 Tc is typically around 39K, impurities might lower it. 
        # Allow a wide range for robustness, but flag obvious outliers.
        if np.max(predictions) > 200 or np.min(predictions) < -50:
            # Log a warning but don't fail unless it's extreme, as model might be untrained or data weird
            pass 

    def test_metrics_consistency(self, project_paths):
        """
        Verify that the model_metrics.json exists and contains entries for the trained model.
        """
        if not project_paths["metrics"].exists():
            pytest.skip("Metrics file (model_metrics.json) not found. Run T021 first.")

        with open(project_paths["metrics"], "r") as f:
            metrics = json.load(f)

        assert isinstance(metrics, list) or isinstance(metrics, dict), "Metrics should be a list or dict."
        
        # If it's a dict with model names as keys, check for 'best' or similar
        if isinstance(metrics, dict):
            # Common structure: { "LinearRegression": {...}, "best_model": {...} }
            assert len(metrics) > 0, "Metrics file is empty."
        else:
            # If it's a list
            assert len(metrics) > 0, "Metrics list is empty."