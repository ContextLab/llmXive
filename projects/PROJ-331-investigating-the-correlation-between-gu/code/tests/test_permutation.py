"""Basic sanity test for the permutation module.

The test runs the permutation routine on a tiny synthetic dataset
(generated on‑the‑fly) with only two taxa and three patients. It checks
that the output CSV is created and that all empirical p‑values lie in the
interval [0, 1].
"""
from __future__ import annotations

import os
import tempfile

import pandas as pd
import pytest

from code.src.pipeline import permutation, preprocess, ingest

@pytest.fixture
def tiny_dataset(tmp_path: str):
    """Create minimal ASV and clinical files."""
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

def test_permutation_runs(tiny_dataset, tmp_path):
    asv_path, clin_path = tiny_dataset

    # Run ingest validation (writes validation JSON)
    ingest.main(asv_path, clin_path, tmp_path / "ingest_validation.json")

    # Run preprocessing (writes CLR and filtered files)
    preprocess.run_preprocess(asv_path, clin_path, out_dir=tmp_path / "processed", max_taxa=10)

    # Run permutation with a tiny number of iterations for speed
    out_csv = tmp_path / "permutation_pvalues.csv"
    permutation.run_permutation(
        iterations=10,
        seed=123,
        clr_path=tmp_path / "processed" / "clr_abundances.parquet",
        clinical_path=clin_path,
        out_path=out_csv,
        max_wall_seconds=60,
    )

    assert out_csv.is_file()
    df = pd.read_csv(out_csv)
    assert set(df.columns) == {"taxon_name", "empirical_p"}
    # All empirical p‑values must be within [0, 1].
    assert df["empirical_p"].between(0, 1).all()