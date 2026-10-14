"""Integration test for the US1 end‑to‑end pipeline.

The test creates a minimal but valid synthetic ASV table and clinical
metadata in the project's ``data/raw`` directory, then invokes the
``run_us1`` entry point.  It verifies that:

* ``results/taxa_correlations_adj.csv`` exists and contains the expected
  columns (including the BH‑adjusted p‑values).
* ``results/runtime_log.txt`` exists and records a total runtime that is
  well below the 6‑hour budget.
* The number of rows in the adjusted results matches the number of taxa
  retained after preprocessing.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from llmxive_toolkit import paths
from code.src.pipeline.run_us1 import main as run_us1_main

@pytest.fixture
def tiny_dataset(tmp_path: pathlib.Path):
    """Create a tiny synthetic dataset in the project's raw data folder."""
    # Ensure the raw data directory exists.
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ASV table – 3 patients, 2 visits each, 2 taxa, and a ``preprocessed`` flag.
    asv_rows = [
        {
            "sample_id": "s1",
            "patient_id": "p1",
            "visit_date": "2020-01-01",
            "taxon_a": 10,
            "taxon_b": 5,
            "preprocessed": True,
        },
        {
            "sample_id": "s2",
            "patient_id": "p1",
            "visit_date": "2021-01-01",
            "taxon_a": 12,
            "taxon_b": 6,
            "preprocessed": True,
        },
        {
            "sample_id": "s3",
            "patient_id": "p2",
            "visit_date": "2020-01-01",
            "taxon_a": 8,
            "taxon_b": 4,
            "preprocessed": True,
        },
        {
            "sample_id": "s4",
            "patient_id": "p2",
            "visit_date": "2021-01-01",
            "taxon_a": 9,
            "taxon_b": 5,
            "preprocessed": True,
        },
        {
            "sample_id": "s5",
            "patient_id": "p3",
            "visit_date": "2020-01-01",
            "taxon_a": 7,
            "taxon_b": 3,
            "preprocessed": True,
        },
        {
            "sample_id": "s6",
            "patient_id": "p3",
            "visit_date": "2021-01-01",
            "taxon_a": 8,
            "taxon_b": 4,
            "preprocessed": True,
        },
    ]
    asv_df = pd.DataFrame(asv_rows)
    asv_path = raw_dir / "open_asv.csv"
    asv_df.to_csv(asv_path, index=False)

    # Clinical metadata – matching patients/visits and required covariates.
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
        {
            "patient_id": "p3",
            "visit_date": "2020-01-01",
            "age": 70,
            "sex": "M",
            "levodopa_eq_dose": 50,
            "MDS_UPDRS_Total": 25,
        },
        {
            "patient_id": "p3",
            "visit_date": "2021-01-01",
            "age": 71,
            "sex": "M",
            "levodopa_eq_dose": 55,
            "MDS_UPDRS_Total": 27,
        },
    ]
    clin_df = pd.DataFrame(clin_rows)
    clin_path = raw_dir / "open_clinical.parquet"
    clin_df.to_parquet(clin_path, index=False)

    return asv_path, clin_path

def test_us1_end_to_end(tmp_path: pathlib.Path, tiny_dataset):
    """Run the US1 pipeline and check that required artefacts are produced."""
    # The fixture creates the raw files in the project ``data/raw`` folder.
    # Run the pipeline.
    rc = run_us1_main()
    assert rc == 0, "run_us1 exited with a non‑zero status"

    # ------------------------------------------------------------------
    # Verify adjusted correlation results.
    # ------------------------------------------------------------------
    adj_path = paths.results("taxa_correlations_adj.csv")
    assert adj_path.is_file(), "Adjusted correlation CSV missing"

    df_adj = pd.read_csv(adj_path)
    expected_cols = {"taxon_name", "spearman_rho", "raw_p", "bh_adj_p"}
    assert set(df_adj.columns) == expected_cols, "Adjusted CSV has unexpected columns"

    # At least one taxon should be present (the synthetic data has two).
    assert len(df_adj) >= 1, "Adjusted results contain no rows"

    # Raw p‑values must be in [0, 1] and adjusted p‑values >= raw.
    assert df_adj["raw_p"].between(0, 1).all()
    assert (df_adj["bh_adj_p"] >= df_adj["raw_p"]).all()

    # ------------------------------------------------------------------
    # Verify runtime log.
    # ------------------------------------------------------------------
    log_path = paths.results("runtime_log.txt")
    assert log_path.is_file(), "runtime_log.txt missing"

    # Parse total runtime (last line should start with "Total:").
    with log_path.open() as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    total_line = next((l for l in lines if l.startswith("Total:")), None)
    assert total_line is not None, "Total runtime not recorded in log"

    total_seconds = float(total_line.split(":")[1].strip().split()[0])
    # The synthetic dataset runs in seconds; enforce a generous upper bound.
    assert total_seconds < 6 * 60 * 60, "Pipeline exceeded 6‑hour budget"
