import json
from pathlib import Path

def test_gpr_model_artifact_exists():
    model_path = Path(__file__).parents[2] / "results" / "model" / "gpr_model.joblib"
    assert model_path.is_file(), f"GPR model artifact not found at {model_path}"

def test_baseline_model_artifact_exists():
    model_path = Path(__file__).parents[2] / "results" / "model" / "baseline_model.joblib"
    assert model_path.is_file(), f"Baseline model artifact not found at {model_path}"

def test_metrics_file_exists_and_contains_required_keys():
    metrics_path = Path(__file__).parents[2] / "results" / "metrics.json"
    assert metrics_path.is_file(), f"Metrics file not found at {metrics_path}"
    with open(metrics_path) as f:
        data = json.load(f)
    required_keys = {
        "gpr_r2", "gpr_rmse", "gpr_mae",
        "baseline_r2", "baseline_rmse", "baseline_mae",
        "gpr_vs_baseline_delta", "rmse_percentage_range"
    }
    missing = required_keys - data.keys()
    assert not missing, f"Metrics JSON missing keys: {missing}"