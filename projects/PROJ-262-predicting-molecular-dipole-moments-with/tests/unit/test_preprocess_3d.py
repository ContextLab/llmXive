"""Unit test for the 3‑D preprocessing script.

The test simply runs the script with a tiny sample size and checks that
the expected Parquet file is created and contains the required columns.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("samples", [5])
def test_preprocess_creates_parquet(tmp_path: Path, samples: int):
    # Build the command line – we point the output into the temporary directory
    script_path = Path(__file__).parents[3] / "code" / "data" / "preprocess_3d.py"
    output_path = tmp_path / "molecules.parquet"

    cmd = [
        sys.executable,
        str(script_path),
        f"--samples={samples}",
        f"--seed=123",
        f"--output={output_path}",
    ]

    # Run the script; it should exit with status 0
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify the Parquet file exists
    assert output_path.is_file(), "Output Parquet file was not created."

    # Verify required columns are present
    import pandas as pd

    df = pd.read_parquet(output_path)
    expected_columns = {"molecule_id", "atom_numbers", "positions", "bond_index"}
    assert expected_columns.issubset(set(df.columns)), "Missing expected columns"
    assert len(df) == samples, "Unexpected number of rows in the output"