"""
Simple integration test for the ingestion pipeline (T048).

The test runs the ``code/main.py`` script with the ``--full`` flag and then
asserts that the required artefacts exist and contain the minimal amount of
data.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def run_main():
    cmd = [sys.executable, str(PROJECT_ROOT / "code" / "main.py"), "--full"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return result

def test_ingestion_produces_merged_csv():
    result = run_main()
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    merged_path = PROJECT_ROOT / "data" / "intermediate" / "merged.csv"
    assert merged_path.is_file(), "merged.csv was not created"
    # Verify at least 20 rows with required columns
    import pandas as pd
    df = pd.read_csv(merged_path)
    valid = df["yield_strength_MPa"].notna() & df["shear_modulus_GPa"].notna()
    assert valid.sum() >= 20, f"Only {valid.sum()} valid rows found (minimum 20 required)"

def test_checksums_file_created():
    result = run_main()
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    checksums_path = PROJECT_ROOT / "data" / "provenance" / "checksums.txt"
    assert checksums_path.is_file(), "checksums.txt was not created"
    # Basic sanity: file should contain at least one line
    with checksums_path.open() as f:
        lines = f.readlines()
    assert len(lines) >= 1, "checksums.txt appears empty"