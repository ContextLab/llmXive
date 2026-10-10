"""
Unit tests for composition normalization utilities.
"""

import pandas as pd
import numpy as np

from src.data.normalize import normalize_dataframe, get_composition_columns


def test_normalize_simple_dataframe():
    """A tiny dataframe should be normalized so each row sums to 1.0."""
    df = pd.DataFrame({
        "elem_Fe": [0.2, 0.3],
        "elem_Ni": [0.3, 0.4],
        "elem_Cr": [0.5, 0.3]
    })
    normalized_df, _ = normalize_dataframe(df, composition_cols=None, log_adjustments=False)
    comp_cols = get_composition_columns(normalized_df, prefix="elem_")
    row_sums = normalized_df[comp_cols].sum(axis=1).values
    assert np.allclose(row_sums, np.ones_like(row_sums)), "Rows do not sum to 1 after normalization"
