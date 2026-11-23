"""Integration test for the default‑output preprocessing script.

This test runs the ``run_preprocess_default.py`` script, which should
produce the two required parquet files under ``data/processed``.  It then
performs a few sanity checks to ensure the outputs have the expected
shape and basic compositional properties.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(180)
def test_preprocess_writes_default_files(tmp_path: pathlib.Path):
    # Ensure a clean environment: remove any existing processed files.
    processed_dir = paths.data("processed")
    for f in processed_dir.iterdir():
        if f.is_file():
            f.unlink()

    # Execute the script that runs the default preprocessing.
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "code.src.pipeline.run_preprocess_default"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that both expected parquet files now exist.
    filtered_path = processed_dir / "filtered_samples.parquet"
    clr_path = processed_dir / "clr_abundances.parquet"
    assert filtered_path.is_file(), "filtered_samples.parquet not created"
    assert clr_path.is_file(), "clr_abundances.parquet not created"

    # Load the outputs and perform minimal checks.
    filtered = pd.read_parquet(filtered_path)
    clr = pd.read_parquet(clr_path)

    # The filtered table must contain the metadata columns.
    for col in ["patient_id", "visit_date", "sample_id"]:
        assert col in filtered.columns

    # The CLR table must have the same number of rows as the filtered table.
    assert len(clr) == len(filtered)

    # Verify the CLR compositional constraint (row sums ≈ 0).
    taxon_cols = [c for c in clr.columns if c not in ("sample_id", "patient_id", "visit_date")]
    row_sums = clr[taxon_cols].sum(axis=1)
    pd.testing.assert_series_equal(
        row_sums.abs(),
        pd.Series([0.0] * len(row_sums), index=row_sums.index),
        check_names=False,
        atol=1e-9,
    )
