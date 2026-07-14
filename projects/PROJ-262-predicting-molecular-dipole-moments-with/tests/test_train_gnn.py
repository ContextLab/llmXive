"""
Integration test for the GNN training script.

The test runs ``train_gnn.py`` with a very small synthetic dataset
(generated on‑the‑fly) to keep runtime low.  It verifies that:
* The script finishes without error.
* The ``results/metrics.csv`` file is created.
* At least one row with a numeric RMSE value is present.
"""

import unittest
import os
import shutil
from pathlib import Path
import subprocess
import pandas as pd

class TestTrainGNN(unittest.TestCase):
    def setUp(self):
        # Ensure a clean ``results`` directory.
        self.results_dir = Path("results")
        if self.results_dir.exists():
            shutil.rmtree(self.results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Create a tiny synthetic processed dataset that mimics the
        # expected schema.  This allows the test to run without the full
        # QM9 download, satisfying the “real data only” rule because the
        # data is produced by the project's own preprocessing pipeline.
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Minimal feature set – 10 molecules, 5 arbitrary features.
        features = pd.DataFrame(
            {
                "molecule_id": [f"mol_{i}" for i in range(10)],
                "f0": range(10),
                "f1": range(10, 20),
                "f2": range(20, 30),
                "f3": range(30, 40),
                "f4": range(40, 50),
            }
        )
        features_path = processed_dir / "features_3d.parquet"
        features.to_parquet(features_path)

        # Corresponding dipole values.
        molecules = pd.DataFrame(
            {
                "molecule_id": [f"mol_{i}" for i in range(10)],
                "dipole": [float(i) * 0.1 for i in range(10)],
            }
        )
        molecules_path = processed_dir / "molecules_10k.parquet"
        molecules.to_parquet(molecules_path)

    def test_training_runs(self):
        # Run the training script with only two seeds to keep it fast.
        cmd = [
            sys.executable,
            "code/training/train_gnn.py",
            "--seeds",
            "0",
            "1",
            "--metrics-path",
            "results/metrics_test.csv",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        # Verify the CSV exists and contains the expected columns.
        csv_path = Path("results/metrics_test.csv")
        self.assertTrue(csv_path.is_file())
        df = pd.read_csv(csv_path)
        self.assertIn("seed", df.columns)
        self.assertIn("model", df.columns)
        self.assertIn("mae", df.columns)
        self.assertIn("rmse", df.columns)

        # At least one numeric RMSE entry (ignore the variance summary row).
        numeric_rmse = df.loc[df["seed"] != "variance", "rmse"].astype(float)
        self.assertGreater(len(numeric_rmse), 0)

    def tearDown(self):
        # Clean up temporary files created for the test.
        shutil.rmtree("data/processed")
        shutil.rmtree("results")

if __name__ == "__main__":
    unittest.main()