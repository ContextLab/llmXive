"""
Test that the metrics produced by ``train_regressor.py`` correctly report the
``meets_sc006`` flag according to the definition:
    meets_sc006 == (val_mse < 0.9 * baseline_mse)
"""
import json
import pathlib

def _load_metrics() -> dict:
    # The metrics file is written to ``data/metrics.json`` relative to the
    # project root.
    metrics_path = pathlib.Path(__file__).parents[2] / "data" / "metrics.json"
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_meets_sc006_logic():
    metrics = _load_metrics()
    # Ensure required keys exist
    for key in ("val_mse", "baseline_mse", "meets_sc006"):
        assert key in metrics, f"Missing key {key} in metrics.json"

    val_mse = metrics["val_mse"]
    baseline_mse = metrics["baseline_mse"]
    expected = val_mse < 0.9 * baseline_mse if baseline_mse > 0 else False
    assert metrics["meets_sc006"] is expected, (
        f"meets_sc006 flag mismatch: expected {expected}, "
        f"got {metrics['meets_sc006']}"
    )