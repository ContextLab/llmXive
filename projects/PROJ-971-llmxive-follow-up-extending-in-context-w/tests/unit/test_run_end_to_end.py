"""
Unit test for the ``src.pipeline.run_end_to_end`` driver.

The test invokes the ``main`` function with a small ``--subset`` value,
then checks that:
  * exactly ``subset`` ``.npz`` files exist under ``data/raw``,
  * the descriptor CSV exists,
  * the CSV contains the expected columns,
  * the number of rows in the CSV equals ``subset``.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

# Import the driver module using its package path.
from src.pipeline import run_end_to_end

@pytest.mark.parametrize("subset", [5, 10])
def test_end_to_end_pipeline(subset: int, monkeypatch):
    """
    Run the pipeline with a small subset and verify artefacts.
    """
    # Ensure a clean environment: remove any pre‑existing files.
    raw_dir = Path("data/raw")
    csv_path = Path("data/descriptors_subset.csv")
    if raw_dir.exists():
        for p in raw_dir.iterdir():
            p.unlink()
    if csv_path.exists():
        csv_path.unlink()

    # Call the driver directly (bypassing argparse) to avoid sys.exit.
    run_end_to_end._run_pipeline(num_clips=subset)

    # 1️⃣  Verify the correct number of clip files.
    assert raw_dir.is_dir()
    clip_files = sorted(p for p in raw_dir.iterdir() if p.suffix == ".npz")
    assert len(clip_files) == subset, f"Expected {subset} clips, found {len(clip_files)}"

    # 2️⃣  Verify the descriptor CSV.
    assert csv_path.is_file()
    df: pd.DataFrame = pd.read_csv(csv_path)
    expected_cols = {"clip_id", "variance", "autocorr_lag1", "spectral_density"}
    assert expected_cols.issubset(df.columns), f"Missing columns: {expected_cols - set(df.columns)}"
    assert len(df) == subset, f"CSV should have {subset} rows, has {len(df)}"