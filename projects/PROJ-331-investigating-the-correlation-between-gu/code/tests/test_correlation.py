"""Tests for the correlation module (Task T004).

This test suite creates a minimal synthetic dataset, runs the full
preprocessing, slope computation, and then the correlation step.
It validates that:
  * The primary results CSV is created.
  * Required columns are present.
  * Raw p‑values are within [0, 1].
  * Benjamini‑Hochberg adjusted p‑values are ≥ raw p‑values.
  * Adjusted p‑values are monotonic non‑decreasing when rows are
    sorted by the raw p‑value (property of BH correction).
  * The optional covariate‑adjusted partial Spearman CSV is written
    when ``partial=True`` and contains the expected columns.
"""

from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from code.src.pipeline import (
    ingest,
    preprocess,
    slopes,
    correlation,
)

@pytest.fixture
def tiny_dataset(tmp_path: pathlib.Path):
    """Create a tiny synthetic ASV and clinical dataset."""
    # ASV: 3 patients, 2 visits each, 2 taxa
    asv_rows = [
        {"sample_id": "s1", "patient_id": "p1", "visit_date": "2020-01-01", "taxon_a": 10, "taxon_b": 5},
        {"sample_id": "s2", "patient_id": "p1", "visit_date": "2021-01-01", "taxon_a": 12, "taxon_b": 6},
        {"sample_id": "s3", "patient_id": "p2", "visit_date": "2020-01-01", "taxon_a": 8, "taxon_b": 4},
        {"sample_id": "s4", "patient_id": "p2", "visit_date": "2021-01-01", "taxon_a": 9, "taxon_b": 5},
        {"sample_id": "s5", "patient_id": "p3", "visit_date": "2020-01-01", "taxon_a": 7, "taxon_b": 3},
        {"sample_id": "s6", "patient_id": "p3", "visit_date": "2021-01-01", "taxon_a": 8, "taxon_b": 4},
    ]
    asv_df = pd.DataFrame(asv_rows)
    asv_path = tmp_path / "ppmi_asv.csv"
    asv_df.to_csv(asv_path, index=False)

    # Clinical: same patients/visits, simple covariates + outcome
    clin_rows = [
        {"patient_id": "p1", "visit_date": "2020-01-01", "age": 60, "sex": "M", "levodopa_eq_dose": 100, "MDS_UPDRS_Total": 30},
        {"patient_id": "p1", "visit_date": "2021-01-01", "age": 61, "sex": "M", "levodopa_eq_dose": 110, "MDS_UPDRS_Total": 35},
        {"patient_id": "p2", "visit_date": "2020-01-01", "age": 65, "sex": "F", "levodopa_eq_dose": 0,   "MDS_UPDRS_Total": 28},
        {"patient_id": "p2", "visit_date": "2021-01-01", "age": 66, "sex": "F", "levodopa_eq_dose": 10,  "MDS_UPDRS_Total": 32},
        {"patient_id": "p3", "visit_date": "2020-01-01", "age": 70, "sex": "M", "levodopa_eq_dose": 50,  "MDS_UPDRS_Total": 25},
        {"patient_id": "p3", "visit_date": "2021-01-01", "age": 71, "sex": "M", "levodopa_eq_dose": 55,  "MDS_UPDRS_Total": 27},
    ]
    clin_df = pd.DataFrame(clin_rows)
    clin_path = tmp_path / "ppmi_clinical.parquet"
    clin_df.to_parquet(clin_path, index=False)

    return asv_path, clin_path

def test_correlation_produces_results(tmp_path: pathlib.Path, tiny_dataset):
    """Run the full pipeline up to correlation and validate the output."""
    asv_path, clin_path = tiny_dataset

    # ------------------------------------------------------------------
    # 1) Ingest validation (writes a JSON report – not needed for the test)
    # ------------------------------------------------------------------
    ingest.main(asv_path, clin_path, tmp_path / "ingest_validation.json")

    # ------------------------------------------------------------------
    # 2) Preprocess – writes filtered_samples.parquet and clr_abundances.parquet
    # ------------------------------------------------------------------
    processed_dir = tmp_path / "processed"
    preprocess.run_preprocess(
        asv_path,
        clin_path,
        out_dir=processed_dir,
        max_taxa=10,
    )

    # ------------------------------------------------------------------
    # 3) Compute slopes – returns paths to the two parquet files
    # ------------------------------------------------------------------
    taxon_slopes_path, outcome_slopes_path = slopes.run_slopes(
        processed_dir / "clr_abundances.parquet",
        clin_path,
    )

    # ------------------------------------------------------------------
    # 4) Run the plain Spearman correlation (partial=False)
    # ------------------------------------------------------------------
    results_path, partial_path = correlation.run_correlation(
        partial=False,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )

    # Verify primary results CSV exists and has correct schema
    assert results_path.is_file()
    df = pd.read_csv(results_path)
    expected_cols = {"taxon_name", "spearman_rho_adj", "raw_p", "bh_adj_p"}
    assert set(df.columns) == expected_cols

    # Raw p‑values must be within [0, 1]
    assert df["raw_p"].between(0, 1).all()

    # BH‑adjusted p‑values must be >= raw p‑values (FDR never decreases p)
    assert (df["bh_adj_p"] >= df["raw_p"]).all()

    # When sorted by raw p, adjusted p‑values should be non‑decreasing
    df_sorted = df.sort_values("raw_p")
    assert df_sorted["bh_adj_p"].is_monotonic_increasing

    # ------------------------------------------------------------------
    # 5) Run the covariate‑adjusted (partial) version and check its file
    # ------------------------------------------------------------------
    _, partial_path = correlation.run_correlation(
        partial=True,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )
    assert partial_path is not None
    assert partial_path.is_file()
    df_partial = pd.read_csv(partial_path)
    expected_partial_cols = {"taxon_name", "spearman_rho_adj", "raw_p"}
    assert set(df_partial.columns) == expected_partial_cols

    # The partial results should differ from the unadjusted ones when covariates vary
    # (simple sanity check: at least one rho value is not identical)
    assert not df["spearman_rho_adj"].equals(df_partial["spearman_rho_adj"])