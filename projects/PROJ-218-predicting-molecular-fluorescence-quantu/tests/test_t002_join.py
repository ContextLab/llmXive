"""
Integration test for ``src.preprocessing.join`` (Task T002).

The test verifies that:
  * The script runs without error.
  * The output file ``data/processed/joined.csv`` is created.
  * The resulting CSV contains an ``inchi_key`` column.
  * At least 200 rows are present (the script itself would raise otherwise).
  * A ``metadata`` column exists.
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd

def test_join_produces_valid_csv(tmp_path):
    # Resolve project‑relative paths
    smiles = Path("data/raw/smiles.parquet")
    fqy = Path("data/raw/fqy.json")
    output = Path("data/processed/joined.csv")

    # Ensure a clean state
    if output.exists():
        output.unlink()

    # Run the join module
    cmd = [
        sys.executable,
        "-m",
        "src.preprocessing.join",
        "--smiles",
        str(smiles),
        "--fqy",
        str(fqy),
        "--output",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0, f"Join script failed: {result.stderr}"

    # Load the produced CSV
    df = pd.read_csv(output)

    # Basic schema checks
    assert "inchi_key" in df.columns, "Missing 'inchi_key' column"
    assert "metadata" in df.columns, "Missing 'metadata' column"

    # Row count (the script itself enforces >=200)
    assert len(df) >= 200, f"Expected at least 200 rows, got {len(df)}"
