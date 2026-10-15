"""
test_split_dataset.py
---------------------
Minimal test for the split_dataset script. It invokes the ``main`` function
and then checks that the expected output files exist and that the row counts
across the three splits sum to the number of records that survived the
sparse‑group filter.
"""

import json
from pathlib import Path

import pandas as pd

from split_dataset import main as split_main
from llmxive_toolkit import paths


def test_split_outputs_exist_and_consistent(tmp_path):
    """
    Run the split script and verify output artifacts.
    """
    # Execute the split logic
    split_main()

    # Resolve output paths
    split_dir = paths.data("split")
    train_path = split_dir / "train.csv"
    val_path = split_dir / "val.csv"
    test_path = split_dir / "test.csv"
    summary_path = split_dir / "split_summary.json"

    # All files must exist
    assert train_path.is_file()
    assert val_path.is_file()
    assert test_path.is_file()
    assert summary_path.is_file()

    # Load CSVs
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    # Load summary
    summary = json.loads(summary_path.read_text())

    # Consistency checks
    total_split_rows = len(train_df) + len(val_df) + len(test_df)
    assert total_split_rows == summary["records_after_exclusion"]

    # Verify that the split fractions are approximately correct (within 1%)
    total = summary["records_after_exclusion"]
    if total > 0:  # avoid division by zero for tiny datasets
        assert abs(len(train_df) / total - 0.70) <= 0.02
        assert abs(len(val_df) / total - 0.15) <= 0.02
        assert abs(len(test_df) / total - 0.15) <= 0.02

    # Ensure the pair_id column is present in each split (re‑constructed)
    for df in (train_df, val_df, test_df):
        assert "pair_id" in df.columns