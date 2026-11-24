"""Integration test for the US1 pipeline wrapper.

The test creates a minimal synthetic dataset in the *default* raw
locations, invokes ``code.src.pipeline.run_us1.main`` and checks that
the expected result file ``data/results/taxa_correlations.csv`` is
produced with the correct schema and row count.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from llmxive_toolkit import paths
from code.src.pipeline import run_us1

@pytest.fixture
def synthetic_dataset(tmp_path: pathlib.Path, monkeypatch):
    """Create a tiny ASV CSV and clinical Parquet in the default raw folder."""
    # Redirect the project root so that ``paths.data`` points inside the temporary directory.
    monkeypatch.setattr(paths, "root", tmp_path, raising=False)

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ASV table – two patients, two visits each, two taxa.
    asv_rows = [
        {"sample_id": "s1", "patient_id": "p1", "visit_date": "2020-01-01", "taxon_a": 10, "taxon_b": 5},
        {"sample_id": "s2", "patient_id": "p1", "visit_date": "2021-01-01", "taxon_a": 12, "taxon_b": 6},
        {"sample_id": "s3", "patient_id": "p2", "visit_date": "2020-01-01", "taxon_a": 8, "taxon_b": 4},
        {"sample_id": "s4", "patient_id": "p2", "visit_date": "2021-01-01", "taxon_a": 9, "taxon_b": 5},
    ]
    asv_df = pd.DataFrame(asv_rows)
    asv_path = raw_dir / "ppmi_asv.csv"
    asv_df.to_csv(asv_path, index=False)

    # Clinical metadata – includes required outcome column.
    clin_rows = [
        {"patient_id": "p1", "visit_date": "2020-01-01", "age": 60, "sex": "M", "levodopa_eq_dose": 100, "MDS_UPDRS_Total": 30},
        {"patient_id": "p1", "visit_date": "2021-01-01", "age": 61, "sex": "M", "levodopa_eq_dose": 110, "MDS_UPDRS_Total": 35},
        {"patient_id": "p2", "visit_date": "2020-01-01", "age": 65, "sex": "F", "levodopa_eq_dose": 0,   "MDS_UPDRS_Total": 28},
        {"patient_id": "p2", "visit_date": "2021-01-01", "age": 66, "sex": "F", "levodopa_eq_dose": 10,  "MDS_UPDRS_Total": 32},
    ]
    clin_df = pd.DataFrame(clin_rows)
    clin_path = raw_dir / "ppmi_clinical.parquet"
    clin_df.to_parquet(clin_path, index=False)

    return asv_path, clin_path

def test_us1_pipeline_produces_correlation_results(synthetic_dataset):
    """Run the US1 wrapper and verify the correlation CSV."""
    # The synthetic data are already placed in the default raw folder by the fixture.
    exit_code = run_us1.main()
    assert exit_code == 0

    # The primary results file should exist under ``data/results``.
    results_path = paths.results("taxa_correlations.csv")
    assert results_path.is_file()

    df = pd.read_csv(results_path)
    expected_cols = {"taxon_name", "spearman_rho", "raw_p", "bh_adj_p"}
    assert set(df.columns) == expected_cols

    # With two taxa we expect exactly two rows.
    assert len(df) == 2
    # Basic sanity checks on value ranges.
    assert df["raw_p"].between(0, 1).all()
    assert df["bh_adj_p"].between(0, 1).all()
    # Adjusted p‑values must be >= raw p‑values.
    assert (df["bh_adj_p"] >= df["raw_p"]).all()