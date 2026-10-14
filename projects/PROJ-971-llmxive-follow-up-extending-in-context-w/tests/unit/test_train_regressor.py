import json
import pathlib

from src.pipeline.train_regressor import main as train_main

def test_train_regressor_metrics(tmp_path, monkeypatch):
    """
    Run the training script with the default dataset and verify that the
    produced ``metrics.json`` satisfies SC‑006 (val_mse < 0.9 * baseline_mse).
    """
    # Ensure the script writes to the project's data directory.
    # The paths utility creates the directory hierarchy automatically.
    # Run the script (it will read the existing CSV files).
    train_main([])

    metrics_path = pathlib.Path("data/metrics.json")
    assert metrics_path.is_file(), "metrics.json was not created"

    with open(metrics_path) as f:
        metrics = json.load(f)

    # The script must set the flag correctly.
    assert metrics["meets_sc006"], (
        f"SC‑006 not met: val_mse={metrics['val_mse']} "
        f"baseline_mse={metrics['baseline_mse']}"
    )