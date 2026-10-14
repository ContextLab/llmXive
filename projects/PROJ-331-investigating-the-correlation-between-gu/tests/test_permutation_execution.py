"""Integration test for the ``run_permutation`` entry‑point.

This test creates a tiny synthetic dataset (the same fixture used in
``code/tests/test_permutation.py``), runs the full command‑line entry point
``python -m src.pipeline.run_permutation`` with explicit ``--clr`` and
``--clinical`` arguments pointing at the generated files, and checks that
the expected CSV is created and contains valid empirical p‑values.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

@pytest.fixture
def tiny_dataset(tmp_path: Path):
    """Create the minimal ASV and clinical files used by the permutation tests."""
    # ASV data – 3 patients, 2 visits each, 2 taxa
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

    # Clinical data – matching patients/visits with covariates + outcome
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

def test_run_permutation_cli(tiny_dataset, tmp_path):
    asv_path, clin_path = tiny_dataset

    # Run ingest and preprocessing to generate the CLR parquet.
    from code.src.pipeline import ingest, preprocess, slopes

    ingest.main(asv_path, clin_path, tmp_path / "ingest_validation.json")
    preprocess.run_preprocess(asv_path, clin_path, out_dir=tmp_path / "processed", max_taxa=10)

    clr_path = tmp_path / "processed" / "clr_abundances.parquet"

    # Execute the entry‑point script with explicit file arguments.
    cmd = [
        sys.executable,
        "-m",
        "src.pipeline.run_permutation",
        "--iterations",
        "10",
        "--seed",
        "123",
        "--clr",
        str(clr_path),
        "--clinical",
        str(clin_path),
        "--out",
        str(tmp_path / "permutation_pvalues.csv"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Verify that the script exited cleanly.
    assert result.returncode == 0

    out_csv = tmp_path / "permutation_pvalues.csv"
    assert out_csv.is_file()
    df = pd.read_csv(out_csv)
    assert set(df.columns) == {"taxon_name", "empirical_p"}
    # All empirical p‑values must be within [0, 1].
    assert df["empirical_p"].between(0, 1).all()