"""Basic sanity test for the ``generate_processed_data`` script.

The test runs the script with a tiny subset size to ensure that the three
expected Parquet files are created and contain the correct columns.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

def test_generate_processed_data(tmp_path: Path):
    # Run the script with a small subset to keep the test fast
    cmd = [
        sys.executable,
        "code/data/generate_processed_data.py",
        "--output-dir",
        str(tmp_path / "processed"),
        "--subset-size",
        "100",
        "--seed",
        "123",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify the three parquet files exist
    molecules_path = tmp_path / "processed" / "molecules_10k.parquet"
    features_3d_path = tmp_path / "processed" / "features_3d.parquet"
    features_2d_path = tmp_path / "processed" / "features_2d.parquet"

    for p in (molecules_path, features_3d_path, features_2d_path):
        assert p.is_file(), f"Missing expected output file: {p}"

    # Load and perform minimal sanity checks
    molecules = pd.read_parquet(molecules_path)
    assert list(molecules.columns) == ["molecule_id", "smiles"]
    assert len(molecules) == 100

    features_3d = pd.read_parquet(features_3d_path)
    assert list(features_3d.columns) == ["molecule_id", "coords_flat"]
    assert len(features_3d) == 100

    features_2d = pd.read_parquet(features_2d_path)
    expected_2d_cols = [
        "molecule_id",
        "smiles_length",
        "num_C",
        "num_N",
        "num_O",
        "num_H",
        "num_rings",
    ]
    assert list(features_2d.columns) == expected_2d_cols
    assert len(features_2d) == 100