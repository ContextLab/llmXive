"""
Basic integration test for the T002 download‑preprocess pipeline.
It runs the ``download_preprocess`` stage and checks that the expected
artefacts are created on disk.
"""
import os
import pathlib

import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(300)
def test_download_preprocess_creates_outputs(tmp_path):
    # Run the pipeline stage
    import subprocess, sys
    repo_root = pathlib.Path(__file__).parents[2]  # project root
    cmd = [sys.executable, "-m", "code.main", "--stage", "download_preprocess"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify checksum file
    checksum_path = paths.data("raw", "checksums.json")
    assert checksum_path.is_file(), "checksums.json not created"

    # Verify a timeseries file exists
    ts_dir = paths.data("processed", "timeseries")
    assert ts_dir.is_dir(), "timeseries directory missing"
    ts_files = list(ts_dir.glob("*_ts.npy"))
    assert len(ts_files) >= 1, "No .npy timeseries files found"

    # Verify exclusion log
    excl_path = paths.data("processed", "exclusion_log.csv")
    assert excl_path.is_file(), "exclusion_log.csv not created"

    # Verify merged dataset
    merged_path = paths.data("processed", "merged_dataset.csv")
    assert merged_path.is_file(), "merged_dataset.csv not created"

    # Basic sanity check on the merged CSV schema
    import pandas as pd
    df = pd.read_csv(merged_path)
    required_cols = {"Subject_ID", "Mean_FD", "Age", "Sex", "Total_Scan_Time", "Flexibility_Score"}
    assert required_cols.issubset(set(df.columns)), "Merged CSV missing required columns"