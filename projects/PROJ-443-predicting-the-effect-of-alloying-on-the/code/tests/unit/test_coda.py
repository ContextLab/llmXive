"""
Unit tests for the ILR (Isometric Log‑Ratio) transformation utilities.
"""

import numpy as np
import pandas as pd

from features.coda import ilr_transform, ilr_inverse, ilr_transform_dataframe


def test_ilr_transform_inverse_roundtrip():
    """Transform a composition to ILR space and back – should recover the original."""
    composition = np.array([0.25, 0.25, 0.25, 0.25])
    ilr_coords = ilr_transform(composition)
    recovered = ilr_inverse(ilr_coords)
    assert np.allclose(composition, recovered, atol=1e-8)


def test_ilr_transform_dataframe():
    """DataFrame version should add ILR columns with expected shape."""
    df = pd.DataFrame({
        "Fe": [0.3, 0.2],
        "Ni": [0.4, 0.5],
        "Cr": [0.3, 0.3]
    })
    result = ilr_transform_dataframe(df, composition_columns=["Fe", "Ni", "Cr"])
    # Original columns remain
    assert set(["Fe", "Ni", "Cr"]).issubset(result.columns)
    # ILR columns added: D-1 = 2 columns named ilr_0, ilr_1
    ilr_cols = [col for col in result.columns if col.startswith("ilr_")]
    assert len(ilr_cols) == 2
    # Values should be finite numbers
    assert np.isfinite(result[ilr_cols].values).all()
