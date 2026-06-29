"""Contract test for controlling the false discovery rate (FDR) after
applying the Benjamini–Hochberg correction.

The test expects a CSV file at ``data/model/corrected_pvalues.csv`` that
contains the adjusted p‑values produced by the pipeline (task T029).  It
verifies that the proportion of discoveries (adjusted p‑value ≤ 0.05)
does not exceed the target FDR of 0.05.
"""

import pathlib

import pandas as pd
import pytest

@pytest.mark.contract
def test_fdr_is_controlled_at_5_percent():
    """
    Load the corrected p‑values file, locate the column that holds the
    Benjamini–Hochberg adjusted p‑values, and assert that the estimated
    false discovery rate is ≤ 0.05.

    The adjusted‑p‑value column is identified heuristically: any column
    whose name contains ``adj`` or ``fdr`` (case‑insensitive) is treated
    as the adjusted p‑value column.
    """
    # Resolve the path to the CSV produced by the modeling pipeline.
    csv_path = (
        pathlib.Path(__file__).resolve()
        .parents[2]  # go from tests/contract/ to project root
        / "data"
        / "model"
        / "corrected_pvalues.csv"
    )
    assert csv_path.is_file(), f"Corrected p‑values file not found at {csv_path}"

    # Load the CSV.
    df = pd.read_csv(csv_path)

    # Identify the adjusted‑p‑value column.
    candidate_cols = [
        col
        for col in df.columns
        if ("adj" in col.lower()) or ("fdr" in col.lower())
    ]
    assert candidate_cols, (
        "Adjusted p‑value column not found in CSV. Expected a column "
        "containing 'adj' or 'fdr' in its name."
    )
    adj_col = candidate_cols[0]

    # Compute the proportion of discoveries at the conventional α = 0.05.
    discoveries = (df[adj_col] <= 0.05).mean()

    # The Benjamini–Hochberg procedure guarantees that the expected
    # false discovery rate does not exceed the chosen level (0.05).
    # We enforce this as a contract.
    assert discoveries <= 0.05 + 1e-8, (
        f"Estimated FDR ({discoveries:.4f}) exceeds the allowed "
        "threshold of 0.05 after BH correction."
    )