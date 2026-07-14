"""
Basic sanity test for ``code/data/generate_processed_data.py``.

The test checks that the script creates the three required Parquet files
when the prerequisite CSV artefacts are present.  It uses a temporary
directory so that the real project data are left untouched.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from data.generate_processed_data import main as generate_main


@pytest.fixture
def dummy_processed_dir(tmp_path: Path) -> Path:
    """
    Set up a minimal ``data/processed`` hierarchy with dummy CSV files
    containing a small subset of molecules.
    """
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)

    # Create a tiny subset ID list (2 molecules)
    subset_ids = processed / "subset_ids.txt"
    subset_ids.write_text("mol1\nmol2\n")

    # Dummy 3‑D feature CSV
    df_3d = pd.DataFrame(
        {
            "molecule_id": ["mol1", "mol2", "mol3"],
            "feature_a": [0.1, 0.2, 0.3],
            "dipole": [1.0, 2.0, 3.0],
        }
    )
    df_3d.to_csv(processed / "3d_features.csv", index=False)

    # Dummy 2‑D feature CSV
    df_2d = pd.DataFrame(
        {
            "molecule_id": ["mol1", "mol2", "mol3"],
            "fp_0": [0, 1, 0],
            "fp_1": [1, 0, 1],
        }
    )
    df_2d.to_csv(processed / "2d_features.csv", index=False)

    return processed


def test_generate_processed_data_creates_parquet_files(dummy_processed_dir: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Run the generator pointing at the temporary directory and verify that the
    three Parquet files are written and contain only the rows from the subset.
    """
    # Force the script to use the temporary ``data/processed`` directory
    monkeypatch.chdir(dummy_processed_dir.parent.parent)  # project root simulated
    # Run the generator
    generate_main()

    # Expected output paths
    molecules_path = dummy_processed_dir / "molecules_10k.parquet"
    features_3d_path = dummy_processed_dir / "features_3d.parquet"
    features_2d_path = dummy_processed_dir / "features_2d.parquet"

    for p in (molecules_path, features_3d_path, features_2d_path):
        assert p.is_file(), f"Expected Parquet file not found: {p}"

    # Load and verify content
    mol_df = pd.read_parquet(molecules_path)
    assert set(mol_df["molecule_id"]) == {"mol1", "mol2"}

    f3d_df = pd.read_parquet(features_3d_path)
    assert set(f3d_df["molecule_id"]) == {"mol1", "mol2"}

    f2d_df = pd.read_parquet(features_2d_path)
    assert set(f2d_df["molecule_id"]) == {"mol1", "mol2"}