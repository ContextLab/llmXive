"""
src/tests/test_train.py
-----------------------

Verifies that the training script produces the expected artefacts:
- ``cv_metrics.json`` conforms to the ``cv_metrics`` portion of the
  ``model_performance.schema.yaml`` contract.
- Model pickle files ``models/rf_cv.pkl`` and ``models/gb_cv.pkl`` exist.
"""

import json
from pathlib import Path

import pytest

from src.models.train import _aggregate_metrics, _compute_fold_metrics

def _dummy_fold_metrics():
    """Create a list of three simple metric dicts for aggregation testing."""
    return [
        {"rmse": 0.5, "mae": 0.4, "r2": 0.8},
        {"rmse": 0.6, "mae": 0.5, "r2": 0.75},
        {"rmse": 0.55, "mae": 0.45, "r2": 0.78},
    ]

def test_aggregate_metrics():
    per_fold = _dummy_fold_metrics()
    agg = _aggregate_metrics(per_fold)
    # Basic sanity checks – values should be floats and within the range of inputs.
    assert isinstance(agg["rmse_mean"], float)
    assert 0.5 <= agg["rmse_mean"] <= 0.6
    assert isinstance(agg["r2_std"], float)

@pytest.mark.integration
def test_training_produces_outputs(tmp_path: Path):
    """
    End‑to‑end integration test: generate a tiny but valid training CSV,
    run the training entry point, and check artefacts.
    """
    # Build a minimal training set (>=5 groups required for 5‑fold CV).
    data = {
        "composition": [f"A{i}B{i}O3" for i in range(5)],
        "formation_energy": [1.0, 1.2, 0.9, 1.1, 1.3],
    }
    # Add descriptor columns (simple constant values).
    for site in ["A", "B", "X"]:
        for desc in [
            "atomic_radius",
            "electronegativity",
            "oxidation_state",
            "valence_electrons",
        ]:
            col = f"{site}_{desc}"
            data[col] = [0.1] * 5
    df = pd.DataFrame(data)

    train_csv = tmp_path / "train.csv"
    df.to_csv(train_csv, index=False)

    metrics_json = tmp_path / "cv_metrics.json"

    # Invoke the training script.
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "src.models.train", str(train_csv), str(metrics_json)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Training script failed: {result.stderr}"

    # Check JSON exists and contains required keys.
    assert metrics_json.is_file()
    content = json.loads(metrics_json.read_text())
    assert "cv_metrics" in content
    for model_name in ("RandomForest", "GradientBoosting"):
        assert model_name in content["cv_metrics"]
        for key in (
            "rmse_mean",
            "rmse_std",
            "mae_mean",
            "mae_std",
            "r2_mean",
            "r2_std",
        ):
            assert key in content["cv_metrics"][model_name]

    # Check model pickle files.
    assert Path("models/rf_cv.pkl").is_file()
    assert Path("models/gb_cv.pkl").is_file()
    # Check checksum file for the metrics JSON.
    checksum_path = Path("data/checksums/cv_metrics.sha256")
    assert checksum_path.is_file()
    # Simple format validation – 64‑char hex string.
    assert len(checksum_path.read_text().strip()) == 64