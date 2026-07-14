"""
Basic integration test for the Random Forest training script.
The test runs the script with a tiny synthetic dataset to verify that
it executes without error and produces the expected output files.
"""

import subprocess
import os
import pandas as pd
import tempfile

from pathlib import Path

def test_train_rf_runs_and_creates_outputs(tmp_path: Path):
    # Create a minimal synthetic dataset in the expected location.
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a tiny dataset with required columns.
    df = pd.DataFrame({
        "molecule_id": [f"mol_{i}" for i in range(10)],
        "features_2d": [list(range(5)) for _ in range(10)],
        "features_3d": [list(range(5)) for _ in range(10)],
        "dipole": [0.1 * i for i in range(10)],
    })
    molecules_path = processed_dir / "molecules_10k.parquet"
    df.to_parquet(molecules_path)

    # Execute the training script.
    result = subprocess.run(
        ["python", "code/training/train_rf.py", "--seeds", "1", "--epochs", "1"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    # The script should exit cleanly.
    assert result.returncode == 0, f"STDERR: {result.stderr}"

    # Verify that the metrics CSV was created.
    metrics_path = Path("results/metrics.csv")
    assert metrics_path.is_file(), "Metrics CSV not generated"

    # Verify that a Random Forest checkpoint was saved.
    checkpoint_path = Path("data/checkpoints/rf_seed_1.pkl")
    assert checkpoint_path.is_file(), "RF checkpoint not generated"

    # Clean up generated files for isolation.
    for p in [metrics_path, checkpoint_path, molecules_path]:
        if p.exists():
            p.unlink()

    # Remove the processed directory if empty.
    try:
        processed_dir.rmdir()
    except OSError:
        pass