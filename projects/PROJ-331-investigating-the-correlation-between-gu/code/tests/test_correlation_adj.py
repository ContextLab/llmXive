"""Tests for covariate‑adjusted Spearman correlation (Task T004).

The test builds a minimal synthetic dataset (the same as used in the contract
test), runs the full pipeline up to slope computation, then invokes the
correlation module with ``partial=True``.  It verifies:

1. The adjusted results file ``results/taxa_correlations_adj.csv`` exists.
2. The file contains the required columns, including ``bh_adj_p``.
3. Benjamini‑Hochberg adjusted p‑values are monotonic with respect to the
   raw p‑values (i.e., sorting by raw_p yields a non‑decreasing sequence of
   bh_adj_p).
4. At least one Spearman rho differs between the plain and adjusted
   analyses, confirming that residualisation took effect.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from code.src.pipeline import ingest, preprocess, slopes, correlation

@pytest.fixture
def synthetic_dataset(tmp_path: pathlib.Path):
    """Create a minimal synthetic dataset matching the contract test."""
    # ASV table
    asv_rows = [
        {
            "sample_id": "s1",
            "patient_id": "p1",
            "visit_date": "2020-01-01",
            "taxon_a": 10,
            "taxon_b": 5,
        },
        {
            "sample_id": "s2",
            "patient_id": "p1",
            "visit_date": "2021-01-01",
            "taxon_a": 12,
            "taxon_b": 6,
        },
        {
            "sample_id": "s3",
            "patient_id": "p2",
            "visit_date": "2020-01-01",
            "taxon_a": 8,
            "taxon_b": 4,
        },
        {
            "sample_id": "s4",
            "patient_id": "p2",
            "visit_date": "2021-01-01",
            "taxon_a": 9,
            "taxon_b": 5,
        },
    ]
    asv_df = pd.DataFrame(asv_rows)
    asv_path = tmp_path / "open_asv.csv"
    asv_df.to_csv(asv_path, index=False)

    # Clinical metadata (includes required covariates)
    clin_rows = [
        {
            "patient_id": "p1",
            "visit_date": "2020-01-01",
            "age": 60,
            "sex": "M",
            "levodopa_eq_dose": 100,
            "MDS_UPDRS_Total": 30,
        },
        {
            "patient_id": "p1",
            "visit_date": "2021-01-01",
            "age": 61,
            "sex": "M",
            "levodopa_eq_dose": 110,
            "MDS_UPDRS_Total": 35,
        },
        {
            "patient_id": "p2",
            "visit_date": "2020-01-01",
            "age": 65,
            "sex": "F",
            "levodopa_eq_dose": 0,
            "MDS_UPDRS_Total": 28,
        },
        {
            "patient_id": "p2",
            "visit_date": "2021-01-01",
            "age": 66,
            "sex": "F",
            "levodopa_eq_dose": 10,
            "MDS_UPDRS_Total": 32,
        },
    ]
    clin_df = pd.DataFrame(clin_rows)
    clin_path = tmp_path / "open_clinical.parquet"
    clin_df.to_parquet(clin_path, index=False)

    return asv_path, clin_path

def _run_full_pipeline(tmp_path: pathlib.Path, asv_path: pathlib.Path, clin_path: pathlib.Path):
    """Run ingest → preprocess → slopes, returning paths to slope files."""
    # Ingest validation (writes a JSON report)
    ingest_report = tmp_path / "ingest_validation.json"
    rc = ingest.main(asv_path, clin_path, ingest_report)
    assert rc == 0

    # Preprocess (writes filtered_samples.parquet and clr_abundances.parquet)
    processed_dir = tmp_path / "processed"
    preprocess.run_preprocess(
        asv_path,
        clin_path,
        out_dir=processed_dir,
        max_taxa=10,
    )

    # Compute slopes
    clr_path = processed_dir / "clr_abundances.parquet"
    taxon_slopes_path, outcome_slopes_path = slopes.run_slopes(
        clr_path,
        clin_path,
    )
    return taxon_slopes_path, outcome_slopes_path

def test_partial_spearman_adjusted(tmp_path: pathlib.Path, synthetic_dataset):
    """Validate covariate‑adjusted Spearman correlation output."""
    asv_path, clin_path = synthetic_dataset

    taxon_slopes_path, outcome_slopes_path = _run_full_pipeline(
        tmp_path, asv_path, clin_path
    )

    # Run plain correlation for reference
    plain_path, _ = correlation.run_correlation(
        partial=False,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )
    plain_df = pd.read_csv(plain_path)

    # Run covariate‑adjusted correlation
    adj_path, _ = correlation.run_correlation(
        partial=True,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
        covariates_path=clin_path,
    )
    adj_df = pd.read_csv(adj_path)

    # 1. File exists and has required columns
    assert adj_path.is_file()
    required_cols = {"taxon_name", "spearman_rho", "raw_p", "bh_adj_p"}
    assert required_cols.issubset(set(adj_df.columns))

    # 2. BH‑adjusted p‑values are monotonic with respect to raw p‑values
    sorted_adj = adj_df.sort_values("raw_p")
    bh_vals = sorted_adj["bh_adj_p"].values
    assert all(bh_vals[i] <= bh_vals[i + 1] for i in range(len(bh_vals) - 1))

    # 3. Residualisation changes at least one rho value compared to plain results
    merged = plain_df.merge(adj_df, on="taxon_name", suffixes=("_plain", "_adj"))
    rho_diff = (merged["spearman_rho_plain"] - merged["spearman_rho_adj"]).abs()
    assert any(rho_diff > 1e-8), "Adjusted rho should differ from plain rho"

    # 4. Adjusted results still contain BH‑adjusted column
    assert "bh_adj_p" in adj_df.columns