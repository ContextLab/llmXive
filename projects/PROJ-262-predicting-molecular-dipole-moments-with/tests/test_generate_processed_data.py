"""Tests for the ``generate_processed_data`` script.

The test suite verifies that the script creates the three expected parquet
files and that they contain the correct columns.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

# The script is designed to be runnable as a module.
from data.generate_processed_data import main as generate_main

@pytest.fixture(scope="module")
def output_dir(tmp_path_factory):
    """Create a temporary directory for script output."""
    return tmp_path_factory.mktemp("processed_data")

def run_script(output_dir: Path) -> None:
    """Execute ``generate_processed_data`` with the provided output directory."""
    # Monkey‑patch sys.argv for argparse
    import sys

    original_argv = sys.argv
    sys.argv = ["generate_processed_data.py", "--output-dir", str(output_dir)]
    try:
        generate_main()
    finally:
        sys.argv = original_argv

def test_generated_files_exist(output_dir: Path):
    """The three parquet files must exist after script execution."""
    run_script(output_dir)

    expected_files = [
        output_dir / "molecules_10k.parquet",
        output_dir / "features_3d.parquet",
        output_dir / "features_2d.parquet",
    ]
    for file_path in expected_files:
        assert file_path.is_file(), f"Missing expected output file: {file_path}"

def test_molecules_file_schema(output_dir: Path):
    """The molecules parquet must contain at least the core columns."""
    run_script(output_dir)

    df = pd.read_parquet(output_dir / "molecules_10k.parquet")
    required = {"molecule_id", "atoms", "coordinates", "dipole"}
    assert required.issubset(set(df.columns)), "Molecules file missing required columns"

def test_feature_files_schema(output_dir: Path):
    """Feature parquet files must contain ``molecule_id`` and at least one feature."""
    run_script(output_dir)

    for feature_file in ["features_3d.parquet", "features_2d.parquet"]:
        df = pd.read_parquet(output_dir / feature_file)
        assert "molecule_id" in df.columns
        # At least one feature column prefixed with ``feat_`` should exist.
        feature_cols = [c for c in df.columns if c.startswith("feat_")]
        assert feature_cols, f"No feature columns found in {feature_file}"