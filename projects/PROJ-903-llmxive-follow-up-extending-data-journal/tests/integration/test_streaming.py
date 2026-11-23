"""
Integration test for the streaming data loader.

This test verifies that processing a dataset in streaming mode produces the same
aggregate statistics (column means) as loading the entire dataset into memory.
It uses the public Hugging Face dataset `scikit-learn/california_housing`,
which is a real CSV‑like dataset containing numeric columns.
"""

import pandas as pd
import numpy as np
import pytest
from datasets import load_dataset

def _compute_full_means() -> pd.Series:
    """
    Load the full dataset into memory and compute column means.
    """
    ds = load_dataset("scikit-learn/california_housing", split="train")
    df = ds.to_pandas()
    # Compute mean for each numeric column
    return df.mean()

def _compute_streaming_means() -> pd.Series:
    """
    Stream the dataset row‑by‑row and compute column means online.
    """
    ds = load_dataset(
        "scikit-learn/california_housing",
        split="train",
        streaming=True,
    )

    # Initialize accumulators on the first row
    sums = None
    count = 0
    column_order = None

    for row in ds:
        # row is a dict of column -> value
        if sums is None:
            # Preserve column order from the first row for deterministic indexing
            column_order = list(row.keys())
            sums = np.zeros(len(column_order), dtype=np.float64)

        values = np.array([row[col] for col in column_order], dtype=np.float64)
        sums += values
        count += 1

    if count == 0:
        raise RuntimeError("Streaming dataset yielded no rows.")

    means = sums / count
    return pd.Series(means, index=column_order)

def test_streaming_loader_produces_same_means():
    """
    Compare the column means from the full‑load approach with the streaming approach.
    The values should match within a tight floating‑point tolerance.
    """
    full_means = _compute_full_means()
    streaming_means = _compute_streaming_means()

    # Align the two Series to ensure identical ordering before comparison
    streaming_means = streaming_means.reindex(full_means.index)

    # Use pandas testing utilities for a robust comparison
    pd.testing.assert_series_equal(
        full_means,
        streaming_means,
        rtol=1e-6,
        atol=1e-8,
        check_names=False,
    )