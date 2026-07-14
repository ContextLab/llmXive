"""
Basic sanity test for the Random Forest training script.

The test checks that the script can be imported and that the ``main`` function
runs without raising an exception when the required processed data files are
present. It does **not** assert on the numerical values of the metrics – those
depend on the real QM9 data and on stochastic training.
"""
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("seed", [0])
def test_train_rf_executes(seed: int, tmp_path: Path):
    """
    Execute ``code/training/train_rf.py`` with a temporary output directory.
    The test creates the minimal required processed data files (empty but
    correctly typed parquet files) so that the script can run end‑to‑end.
    """
    # Create dummy processed data with the expected schema.
    import pandas as pd
    import numpy as np

    processed_dir = Path(__file__).resolve().parents[3] / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Minimal molecule dataframe
    mol_df = pd.DataFrame(
        {
            "molecule_id": [f"mol_{i}" for i in range(10)],
            "dipole": np.random.rand(10),
        }
    )
    mol_path = processed_dir / "molecules_10k.parquet"
    mol_df.to_parquet(mol_path)

    # Minimal 2‑D feature dataframe (10 rows, 5 dummy features)
    feat_df = pd.DataFrame(
        np.random.rand(10, 5),
        columns=[f"f{i}" for i in range(5)],
    )
    feat_df["molecule_id"] = mol_df["molecule_id"]
    feat_path = processed_dir / "features_2d.parquet"
    feat_df.to_parquet(feat_path)

    # Run the training script
    script_path = Path(__file__).resolve().parents[3] / "code" / "training" / "train_rf.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--seeds", "0", "--output-dir", str(tmp_path / "results"), "--checkpoint-dir", str(tmp_path / "checkpoints")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that the expected artefacts were created.
    metrics_file = Path(tmp_path) / "results" / "metrics.csv"
    variance_file = Path(tmp_path) / "checkpoints" / "rf_rmse_variance.csv"
    assert metrics_file.is_file(), "metrics.csv not created"
    assert variance_file.is_file(), "rf_rmse_variance.csv not created"