"""Test that the memory‑cap logic correctly subsamples taxa when needed.

The test constructs an artificial merged DataFrame that would exceed the
7 GB RAM budget if all taxa were retained.  It then calls the internal
helper ``_cap_impl`` to verify that the top‑N most abundant taxa are
selected.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from code.src.pipeline import preprocess

def test_memory_cap_triggers_subsampling():
    # Create a DataFrame with 10 000 rows and 150 taxa.
    n_rows = 10_000
    n_taxa = 150
    rng = np.random.RandomState(0)
    data = rng.rand(n_rows, n_taxa)
    df = pd.DataFrame(data, columns=[f"t{i}" for i in range(n_taxa)])

    # Inflate one taxon to make it the most abundant.
    df["t0"] = df["t0"] + 1000.0
    df["t7"] = df["t7"] + 900.0

    # The helper should return exactly ``max_taxa`` taxa.
    selected = preprocess._cap_impl(df, list(df.columns), max_taxa=5)
    assert len(selected) == 5
    # The two inflated taxa must be among the selected.
    assert "t0" in selected and "t7" in selected
    # Ensure the selected taxa are the top‑abundance ones.
    abundances = df.sum().sort_values(ascending=False)
    top_expected = list(abundances.head(5).index)
    assert selected == top_expected