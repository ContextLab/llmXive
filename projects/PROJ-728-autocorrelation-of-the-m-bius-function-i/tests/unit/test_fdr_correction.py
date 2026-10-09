"""
Unit tests for the Benjamini–Hochberg FDR correction implementation
in ``code/fdr_correction.py``.

The test creates a temporary CSV file with a known set of p‑values,
runs the ``main`` function, and checks that the ``adjusted_p_value``
column is added and that the values match the expected BH output.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np
import pytest

# Import the module as a whole to allow monkey-patching constants
import code.fdr_correction as fdr

def test_bh_algorithm_known_values():
    """Validate the BH algorithm against a manually computed example."""
    # Example p‑values taken from a classic BH illustration.
    pvals = np.array([0.001, 0.04, 0.03, 0.002, 0.05])
    # Rank order: 0.001 (1), 0.002 (2), 0.03 (3), 0.04 (4), 0.05 (5)
    # BH raw: 
    # 0.001 * 5/1 = 0.005
    # 0.002 * 5/2 = 0.005
    # 0.03 * 5/3 = 0.05
    # 0.04 * 5/4 = 0.05
    # 0.05 * 5/5 = 0.05
    # Monotonicity check: [0.005, 0.005, 0.05, 0.05, 0.05]
    # Mapping back to original order [0.001, 0.04, 0.03, 0.002, 0.05]:
    expected = np.array([0.005, 0.05, 0.05, 0.005, 0.05])
    adjusted = fdr._benjamini_hochberg(pvals)
    np.testing.assert_allclose(adjusted, expected, rtol=1e-12)


def test_main_adds_adjusted_column(tmp_path: Path):
    """
    End‑to‑end test that ``main`` reads a CSV, adds the adjusted column,
    and writes the file back in place.
    """
    # Create a tiny CSV with a 'p_value' column.
    csv_path = tmp_path / "autocorr_stats.csv"
    df = pd.DataFrame({
        "interval_start": [1, 2, 3],
        "interval_length": [1000, 1000, 1000],
        "lag": [1, 2, 3],
        "p_value": [0.01, 0.2, 0.5],
    })
    df.to_csv(csv_path, index=False)

    # Patch the module's INPUT_CSV to point at our temporary file.
    original_input = fdr.INPUT_CSV
    try:
        fdr.INPUT_CSV = csv_path

        # Run the main function – it should modify the file in‑place.
        fdr.main()

        # Reload and verify the new column exists.
        result = pd.read_csv(csv_path)
        assert "adjusted_p_value" in result.columns
        # Compute expected adjusted values using the helper directly.
        expected_adj = fdr._benjamini_hochberg(df["p_value"].to_numpy())
        np.testing.assert_allclose(result["adjusted_p_value"], expected_adj)
    finally:
        # Restore the original constant to avoid side effects for other tests.
        fdr.INPUT_CSV = original_input


def test_module_importable():
    assert callable(fdr.main)
    assert callable(fdr._benjamini_hochberg)