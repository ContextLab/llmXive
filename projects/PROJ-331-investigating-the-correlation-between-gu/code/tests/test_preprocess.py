"""Unit tests for the preprocessing module (Task T002)."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.src.pipeline import preprocess


def _make_asv(tmp_path: Path, n_single_visit: int = 1) -> Path:
    rows = []
    # Patient P1: 3 visits; P2: 2 visits; P3: single visit (excluded)
    data = {
        "P1": [("2020-01-01", 10, 0), ("2020-07-01", 20, 5), ("2021-01-01", 30, 10)],
        "P2": [("2020-01-01", 5, 1), ("2021-01-01", 15, 2)],
    }
    for i in range(n_single_visit):
        data[f"S{i}"] = [("2020-01-01", 3, 0)]
    for pid, visits in data.items():
        for j, (date, a, b) in enumerate(visits):
            rows.append(
                {
                    "sample_id": f"{pid}_{j}",
                    "patient_id": pid,
                    "visit_date": date,
                    "taxon_a": a,
                    "taxon_b": b,
                    "taxon_zero": 0,
                }
            )
    path = tmp_path / "ppmi_asv.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path

def _make_clinical(tmp_path: Path) -> Path:
    rows = []
    for pid, dates in {
        "P1": ["2020-01-01", "2020-07-01", "2021-01-01"],
        "P2": ["2020-01-01", "2021-01-01"],
        "S0": ["2020-01-01"],
    }.items():
        for d in dates:
            rows.append(
                {
                    "patient_id": pid,
                    "visit_date": d,
                    "age": 65,
                    "sex": "M",
                    "levodopa_eq_dose": 100,
                    "MDS_UPDRS_Total": 30,
                }
            )
    path = tmp_path / "ppmi_clinical.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_single_visit_patients_excluded_with_logged_count(tmp_path, caplog):
    asv, clin = _make_asv(tmp_path), _make_clinical(tmp_path)
    with caplog.at_level(logging.WARNING):
        summary = preprocess.run_preprocess(asv, clin, out_dir=tmp_path / "out")
    assert summary["cohort_stats"]["excluded_subjects"] == 1
    assert summary["cohort_stats"]["retained_patients"] == 2
    assert "excluded 1 subject" in caplog.text


def test_two_visit_patients_are_retained(tmp_path):
    asv, clin = _make_asv(tmp_path), _make_clinical(tmp_path)
    summary = preprocess.run_preprocess(asv, clin, out_dir=tmp_path / "out")
    clr = pd.read_parquet(tmp_path / "out" / "clr_abundances.parquet")
    assert set(clr["patient_id"]) == {"P1", "P2"}


def test_zero_taxa_dropped_with_warning(tmp_path, caplog):
    asv, clin = _make_asv(tmp_path), _make_clinical(tmp_path)
    with caplog.at_level(logging.WARNING):
        summary = preprocess.run_preprocess(asv, clin, out_dir=tmp_path / "out")
    assert "taxon_zero" not in summary["taxa_retained"]
    assert "all-zero taxon" in caplog.text


def test_clr_output_rows_equal_retained_samples(tmp_path):
    asv, clin = _make_asv(tmp_path), _make_clinical(tmp_path)
    summary = preprocess.run_preprocess(asv, clin, out_dir=tmp_path / "out")
    filtered = pd.read_parquet(tmp_path / "out" / "filtered_samples.parquet")
    clr = pd.read_parquet(tmp_path / "out" / "clr_abundances.parquet")
    assert len(clr) == summary["cohort_stats"]["retained_rows"]
    assert len(filtered) == len(clr)
    # CLR rows sum to ~0 per sample (compositional property)
    taxon_cols = [c for c in clr.columns if c not in ("sample_id", "patient_id", "visit_date")]
    assert np.allclose(clr[taxon_cols].sum(axis=1), 0.0, atol=1e-9)


def test_clr_uses_pseudocount(tmp_path):
    counts = pd.DataFrame({"a": [0.0, 1.0], "b": [4.0, 3.0]})
    out = preprocess.clr_transform(counts)
    la = np.log(0.0 + preprocess.PSEUDOCOUNT)
    lb = np.log(4.0 + preprocess.PSEUDOCOUNT)
    expected_a = la - (la + lb) / 2
    assert np.isclose(out.loc[0, "a"], expected_a)


def test_zero_variance_covariate_detected(tmp_path, caplog):
    asv, clin = _make_asv(tmp_path), _make_clinical(tmp_path)
    # levodopa dose is constant in the fixture -> zero variance
    with caplog.at_level(logging.WARNING):
        summary = preprocess.run_preprocess(asv, clin, out_dir=tmp_path / "out")
    assert "levodopa_eq_dose" in summary["zero_variance_covariates"]
    assert "Zero-variance covariate" in caplog.text


def test_missing_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        preprocess.run_preprocess(tmp_path / "nope.csv", tmp_path / "nope.parquet",
                                  out_dir=tmp_path / "out")


def test_memory_cap_selects_top_taxa(tmp_path):
    merged = pd.DataFrame(np.random.RandomState(0).rand(10, 150))
    merged.columns = [f"t{i}" for i in range(150)]
    merged["t0"] = 1000.0  # most abundant
    merged["t7"] = 900.0
    kept = preprocess.cap_taxa_by_memory(merged, list(merged.columns), max_taxa=5)
    # Force the budget branch by checking the small case does NOT subsample
    assert len(kept) == 150
    # Directly exercise the subsampling logic
    kept_small = preprocess._cap_impl(merged, list(merged.columns), 5)
    assert len(kept_small) == 5
    assert "t0" in kept_small and "t7" in kept_small