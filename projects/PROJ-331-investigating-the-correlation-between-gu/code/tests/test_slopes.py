"""Unit tests for the per-patient slope computation (Task T003)."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.src.pipeline import slopes

def _make_clr_parquet(tmp_path: Path) -> Path:
    """Create a minimal CLR-transformed abundance parquet file.

    Two patients (p1, p2), each with two visits (0 and 1 year).
    Taxa: taxon_a, taxon_b.  A third single-visit patient (p3) is
    included to exercise the >=2-visit inclusion rule.
    """
    data = [
        # patient p1
        {
            "sample_id": "s1",
            "patient_id": "p1",
            "visit_date": "2020-01-01",
            "taxon_a": 0.1,
            "taxon_b": 0.5,
        },
        {
            "sample_id": "s2",
            "patient_id": "p1",
            "visit_date": "2021-01-01",
            "taxon_a": 0.3,
            "taxon_b": 0.7,
        },
        # patient p2
        {
            "sample_id": "s3",
            "patient_id": "p2",
            "visit_date": "2020-06-01",
            "taxon_a": 0.2,
            "taxon_b": 0.4,
        },
        {
            "sample_id": "s4",
            "patient_id": "p2",
            "visit_date": "2021-06-01",
            "taxon_a": 0.4,
            "taxon_b": 0.6,
        },
        # patient p3: single visit -> excluded from slopes
        {
            "sample_id": "s5",
            "patient_id": "p3",
            "visit_date": "2020-01-01",
            "taxon_a": 0.9,
            "taxon_b": 0.9,
        },
    ]
    df = pd.DataFrame(data)
    out_path = tmp_path / "clr_abundances.parquet"
    df.to_parquet(out_path, index=False)
    return out_path

def _make_clinical_parquet(tmp_path: Path, include_outcome: bool = True) -> Path:
    """Create a clinical parquet file with optional MDS_UPDRS_Total column."""
    base = [
        {
            "patient_id": "p1",
            "visit_date": "2020-01-01",
            "age": 65,
            "sex": "M",
            "levodopa_eq_dose": 100,
        },
        {
            "patient_id": "p1",
            "visit_date": "2021-01-01",
            "age": 66,
            "sex": "M",
            "levodopa_eq_dose": 110,
        },
        {
            "patient_id": "p2",
            "visit_date": "2020-06-01",
            "age": 70,
            "sex": "F",
            "levodopa_eq_dose": 0,
        },
        {
            "patient_id": "p2",
            "visit_date": "2021-06-01",
            "age": 71,
            "sex": "F",
            "levodopa_eq_dose": 10,
        },
    ]
    if include_outcome:
        # Simple linear increase: slope = 2 per year
        for row in base:
            year = 0 if row["visit_date"].endswith("01-01") else 0.5
            row["MDS_UPDRS_Total"] = 30 + 2 * year
    df = pd.DataFrame(base)
    out_path = tmp_path / ("ppmi_clinical.parquet" if include_outcome else "clinical_no_outcome.parquet")
    df.to_parquet(out_path, index=False)
    return out_path

def test_compute_taxon_slopes_simple(tmp_path: Path):
    """Verify that taxon slopes equal the manual linear regression result."""
    clr_path = _make_clr_parquet(tmp_path)
    clr_df = pd.read_parquet(clr_path)

    # Expected slopes:
    # For p1: taxon_a changes from 0.1 to 0.3 over 1 year => slope 0.2
    #          taxon_b changes from 0.5 to 0.7 => slope 0.2
    # For p2: taxon_a 0.2 -> 0.4 => slope 0.2
    #          taxon_b 0.4 -> 0.6 => slope 0.2
    expected = {
        ("p1", "taxon_a"): 0.2,
        ("p1", "taxon_b"): 0.2,
        ("p2", "taxon_a"): 0.2,
        ("p2", "taxon_b"): 0.2,
    }

    taxon_cols = ["taxon_a", "taxon_b"]
    slopes_df = slopes.compute_taxon_slopes(clr_df, taxon_columns=taxon_cols)

    for _, row in slopes_df.iterrows():
        key = (row["patient_id"], row["taxon_name"])
        assert np.isclose(row["slope"], expected[key], atol=1e-9)

def test_two_visit_patients_included_single_visit_excluded(tmp_path: Path):
    """Patients with exactly 2 visits ARE included; single-visit patients are not."""
    clr_path = _make_clr_parquet(tmp_path)
    clr_df = pd.read_parquet(clr_path)
    slopes_df = slopes.compute_taxon_slopes(clr_df, taxon_columns=["taxon_a", "taxon_b"])
    patients = set(slopes_df["patient_id"])
    assert "p1" in patients and "p2" in patients  # exactly 2 visits: included
    assert "p3" not in patients                    # single visit: excluded
    assert len(slopes_df) == 4                     # 2 patients x 2 taxa

def test_constant_outcome_yields_zero_slope(tmp_path: Path):
    """A constant outcome must yield a measured slope of 0 (never a substituted value)."""
    clinical_path = _make_clinical_parquet(tmp_path, include_outcome=True)
    clinical_df = pd.read_parquet(clinical_path)
    clinical_df["MDS_UPDRS_Total"] = 30.0  # constant outcome
    out_df = slopes.compute_outcome_slopes(clinical_df)
    for _, row in out_df.iterrows():
        assert np.isclose(row["outcome_slope"], 0.0, atol=1e-12)

def test_compute_outcome_slopes_simple(tmp_path: Path):
    """Check outcome slope calculation matches manual expectation."""
    clinical_path = _make_clinical_parquet(tmp_path, include_outcome=True)
    clinical_df = pd.read_parquet(clinical_path)

    # For patient p1: visits at 0 and 1 year, outcomes 30 and 32 => slope 2
    # For patient p2: visits at 0.5 and 1.5 years (1 year apart), outcomes 31 and 33 => slope 2
    expected = {"p1": 2.0, "p2": 2.0}

    out_df = slopes.compute_outcome_slopes(clinical_df)

    for _, row in out_df.iterrows():
        assert np.isclose(row["outcome_slope"], expected[row["patient_id"]], atol=1e-9)

def test_run_slopes_writes_files(tmp_path: Path):
    """End-to-end run_slopes should create the expected parquet files."""
    clr_path = _make_clr_parquet(tmp_path)
    clinical_path = _make_clinical_parquet(tmp_path, include_outcome=True)

    taxon_path, outcome_path = slopes.run_slopes(clr_path, clinical_path)

    # Both files must exist
    assert taxon_path.is_file()
    assert outcome_path is not None and outcome_path.is_file()

    # Load and perform a sanity check on row counts
    taxon_df = pd.read_parquet(taxon_path)
    outcome_df = pd.read_parquet(outcome_path)

    # There are 2 patients * 2 taxa = 4 rows in taxon slopes
    assert len(taxon_df) == 4
    # One row per patient in outcome slopes
    assert len(outcome_df) == 2

def test_run_slopes_missing_outcome(tmp_path: Path, caplog):
    """When the outcome column is absent, the function should skip outcome slopes."""
    clr_path = _make_clr_parquet(tmp_path)
    clinical_path = _make_clinical_parquet(tmp_path, include_outcome=False)

    with caplog.at_level(logging.WARNING):
        taxon_path, outcome_path = slopes.run_slopes(clr_path, clinical_path)

    # Taxon slopes must still be written
    assert taxon_path.is_file()
    # Outcome path should be None and a warning logged
    assert outcome_path is None
    assert any(
        "Outcome column 'MDS_UPDRS_Total' missing" in rec.message
        for rec in caplog.records
    )
