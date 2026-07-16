import pytest
import pickle
import json
from pathlib import Path

def test_model_saving():
    """Verify model saving."""
    model_2d_path = Path("artifacts/models/model_2d.pkl")
    model_3d_path = Path("artifacts/models/model_3d.pkl")

    assert model_2d_path.exists(), "2D model not saved"
    assert model_3d_path.exists(), "3D model not saved"

    with open(model_2d_path, "rb") as f:
        model_2d = pickle.load(f)
    with open(model_3d_path, "rb") as f:
        model_3d = pickle.load(f)

    assert model_2d is not None, "2D model is None"
    assert model_3d is not None, "3D model is None"

def test_metric_calculation():
    """Verify metric calculation."""
    cv_metrics_path = Path("artifacts/metrics/cv_metrics.json")
    assert cv_metrics_path.exists(), "CV metrics not saved"

    with open(cv_metrics_path, "r") as f:
        metrics = json.load(f)

    assert "model_2d" in metrics, "Model 2D metrics missing"
    assert "model_3d" in metrics, "Model 3D metrics missing"
    assert "mean_mae" in metrics["model_2d"], "MAE missing for model 2D"
    assert "mean_mae" in metrics["model_3d"], "MAE missing for model 3D"