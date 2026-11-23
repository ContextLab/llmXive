import os
import pandas as pd
import numpy as np
import pytest

from code.preprocess import (
    load_gene_coords,
    load_peaks,
    bin_aggregation,
    load_all_counts,
    filter_zero_expression,
    log_transform,
    impute_median,
    merge_features_expression,
    PROC_DIR,
    RAW_DIR,
    CELL_LINES,
)

@pytest.fixture(scope="module")
def gene_coords():
    return load_gene_coords()

@pytest.fixture(scope="module")
def peaks():
    # Load peaks for the first cell line (GM12878) for testing
    return load_peaks(CELL_LINES[0])

def test_bin_aggregation_shape(gene_coords, peaks):
    binned = bin_aggregation(CELL_LINES[0], gene_coords, peaks)
    # Should have one row per gene and 200 bin columns + gene_id
    assert "gene_id" in binned.columns
    bin_cols = [c for c in binned.columns if c.startswith("bin_")]
    assert len(bin_cols) == 200
    assert binned.shape[0] == gene_coords.shape[0]

def test_load_all_counts():
    counts = load_all_counts()
    # Expect 5 cell lines * 2 genes = 10 rows in the synthetic test data
    assert counts.shape[0] == 10
    assert set(counts["cell_line"]) == set(CELL_LINES)

def test_filter_zero_expression():
    counts = load_all_counts()
    filtered = filter_zero_expression(counts)
    # Gene ENSG000002 has zero count in all cell lines → should be removed
    assert "ENSG000002" not in filtered["gene_id"].unique()
    # Gene ENSG000001 should remain
    assert "ENSG000001" in filtered["gene_id"].unique()

def test_log_transform():
    counts = load_all_counts()
    filtered = filter_zero_expression(counts)
    logged = log_transform(filtered)
    assert "log_count" in logged.columns
    # Verify transformation for a known count (123)
    val = logged.loc[logged["count"] == 123, "log_count"].iloc[0]
    assert np.isclose(val, np.log(124))

def test_impute_median():
    # Create a small DataFrame with NaNs
    df = pd.DataFrame({
        "gene_id": ["g1", "g2"],
        "bin_1": [1.0, np.nan],
        "bin_2": [np.nan, 3.0],
    })
    imputed = impute_median(df)
    # Median of bin_1 is 1.0, bin_2 is 3.0
    assert imputed.loc[imputed["gene_id"] == "g2", "bin_1"].iloc[0] == 1.0
    assert imputed.loc[imputed["gene_id"] == "g1", "bin_2"].iloc[0] == 3.0

def test_merge_features_expression(gene_coords, peaks):
    binned = bin_aggregation(CELL_LINES[0], gene_coords, peaks)
    counts = load_all_counts()
    filtered = filter_zero_expression(counts)
    logged = log_transform(filtered)
    merged = merge_features_expression(binned, logged, CELL_LINES[0])
    # Should contain gene_id, 200 bins, and log_expression
    assert "log_expression" in merged.columns
    assert merged.shape[0] == binned.shape[0]
    bin_cols = [c for c in merged.columns if c.startswith("bin_")]
    assert len(bin_cols) == 200