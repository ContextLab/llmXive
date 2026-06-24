"""
test_generate_outputs.py

Integration test for the ``generate_outputs.py`` script (Task T020).

The test invokes the script via a subprocess, then checks that the three
expected Parquet files exist and contain exactly 10 000 rows.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

# Path to the script relative to the repository root
SCRIPT_PATH = Path("code/data/generate_outputs.py")

# Expected output files
OUTPUT_DIR = Path("data/processed")
MOLECULES_FILE = OUTPUT_DIR / "molecules_10k.parquet"
FEATURES_3D_FILE = OUTPUT_DIR / "features_3d.parquet"
FEATURES_2D_FILE = OUTPUT_DIR / "features_2d.parquet"


@pytest.mark.timeout(300)  # ensure the whole pipeline finishes within the CI timeout
def test_generate_outputs_creates_files(tmp_path, monkeypatch):
    """
    Run the data‑generation script and verify that the three Parquet files are
    produced and each contains 10 000 records.
    """
    # Use a temporary directory for outputs to avoid polluting the repo
    monkeypatch.chdir(tmp_path)

    # Run the script
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--size", "1000", "--seed", "123"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify files exist
    for path in (MOLECULES_FILE, FEATURES_3D_FILE, FEATURES_2D_FILE):
        assert path.is_file(), f"Expected output file not found: {path}"

    # Verify row counts (we asked for 1 000 molecules in this test)
    for path in (MOLECULES_FILE, FEATURES_3D_FILE, FEATURES_2D_FILE):
        df = pd.read_parquet(path)
        assert len(df) == 1000, f"Unexpected number of rows in {path}"