"""
Unit tests for the 3‑D preprocessing script.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd

# Import the main function from the script we just created
from code.data.preprocess_3d import main as preprocess_main

def create_dummy_qm9_parquet(path: Path) -> None:
    """
    Create a minimal QM9‑like parquet file with a handful of rows.
    The schema mimics what ``datasets.load_dataset('qm9')`` would produce.
    """
    data = {
        "atom_types": [[6, 1, 1, 1], [8, 1, 1]],
        "coordinates": [
            [[0.0, 0.0, 0.0], [0.0, 0.0, 1.09], [1.02, 0.0, -0.36], [-0.51, 0.89, -0.36]],
            [[0.0, 0.0, 0.0], [0.0, 0.0, 0.96], [0.92, 0.0, -0.24]],
        ],
        "bond_index": [
            [[0, 1], [0, 2], [0, 3]],
            [[0, 1], [0, 2]],
        ],
    }
    df = pd.DataFrame(data)
    df.to_parquet(path, index=False)

def test_preprocess_creates_output():
    # Set up a temporary project‑root‑like directory
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create dummy raw data file
        raw_dir = root / "data" / "raw"
        raw_dir.mkdir(parents=True)
        raw_parquet = raw_dir / "qm9.parquet"
        create_dummy_qm9_parquet(raw_parquet)

        # Change working directory so the script sees the relative paths
        cwd = os.getcwd()
        os.chdir(root)

        try:
            # Run the script; it should read the raw file and write the processed file
            exit_code = preprocess_main([])
            assert exit_code == 0

            out_path = Path("data/processed/features_3d.parquet")
            assert out_path.is_file()

            # Load the output and perform a sanity check
            out_df = pd.read_parquet(out_path)
            assert list(out_df.columns) == [
                "molecule_id",
                "atom_types",
                "coordinates",
                "bonds",
            ]
            assert len(out_df) == 2  # we created two dummy molecules
        finally:
            os.chdir(cwd)