"""Tests for the ``code.filter_missing`` module (Task T016).

The test suite verifies that:
1. The filtered CSV file exists after running the filter.
2. No row in the filtered CSV has an empty, null, or whitespace‑only ``doc_diff``.
3. The filtered CSV contains no more rows than the original raw CSV.
"""
from __future__ import annotations

import pandas as pd

from llmxive_toolkit import paths

from code.filter_missing import filter_missing

def test_filter_missing_creates_valid_csv(tmp_path):
    """
    Run the filter and validate the resulting CSV.
    """
    # Run the filtering logic.
    out_path = filter_missing()
    # Ensure the output path is as expected.
    expected_path = paths.data("processed", "filtered_commit_pairs.csv")
    assert out_path == expected_path
    assert out_path.is_file(), f"Filtered CSV not found at {out_path}"

    # Load both raw and filtered CSVs.
    raw_path = paths.data("raw", "commit_pairs.csv")
    raw_df = pd.read_csv(raw_path, dtype=str)
    filtered_df = pd.read_csv(out_path, dtype=str)

    # 1. No empty or null ``doc_diff`` entries.
    assert "doc_diff" in filtered_df.columns, "'doc_diff' column missing in filtered CSV"
    # Null values
    assert filtered_df["doc_diff"].isnull().sum() == 0, "Null doc_diff entries found"
    # Empty strings or whitespace only
    stripped = filtered_df["doc_diff"].astype(str).str.strip()
    assert (stripped == "").sum() == 0, "Empty or whitespace‑only doc_diff entries found"

    # 2. Row count is less than or equal to the original.
    assert len(filtered_df) <= len(raw_df), (
        f"Filtered rows ({len(filtered_df)}) exceed raw rows ({len(raw_df)})"
    )