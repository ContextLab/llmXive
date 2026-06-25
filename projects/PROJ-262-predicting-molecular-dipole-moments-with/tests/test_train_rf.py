"""Basic sanity test for the Random Forest training script.

The test runs the script with a reduced number of seeds and verifies that
the expected output files are created.
"""
import subprocess
import sys
from pathlib import Path

def test_train_rf_creates_outputs(tmp_path: Path, monkeypatch):
    # Redirect the output directory to a temporary location
    output_dir = tmp_path / "checkpoints"
    output_dir.mkdir(parents=True)

    # Run the training script with 2 seeds for speed
    cmd = [
        sys.executable,
        "code/training/train_rf.py",
        "--num-seeds",
        "2",
        "--output-dir",
        str(output_dir),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=Path.cwd()
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected checkpoint files
    for seed in range(2):
        ckpt = output_dir / f"rf_seed_{seed}.pkl"
        assert ckpt.is_file(), f"Missing checkpoint {ckpt}"

    # Metrics CSV
    metrics_csv = output_dir / "rf_metrics.csv"
    assert metrics_csv.is_file(), "Missing rf_metrics.csv"

    # Verify CSV has the correct columns
    import pandas as pd

    df = pd.read_csv(metrics_csv)
    expected_cols = {"model", "seed", "mae", "rmse"}
    assert expected_cols.issubset(set(df.columns)), "Metrics CSV missing columns"