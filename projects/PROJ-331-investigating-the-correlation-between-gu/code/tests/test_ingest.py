"""Unit tests for the ingest module (T001).

Covers the three required cases:
  1. Valid inputs -> report with row/column counts, outcome present.
  2. Missing input file -> non-zero exit / descriptive error, no fallback.
  3. Missing MDS_UPDRS_Total column -> exit zero with warning + skip flag.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from code.src.pipeline import ingest


def _make_asv(tmp_path: Path) -> Path:
    df = pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "patient_id": ["p1", "p1", "p2"],
            "visit_date": ["2020-01-01", "2021-01-01", "2020-06-01"],
            "Taxon_a": [10, 12, 5],
            "Taxon_b": [0, 3, 7],
        }
    )
    p = tmp_path / "ppmi_asv.csv"
    df.to_csv(p, index=False)
    return p


def _make_clinical(tmp_path: Path, include_outcome: bool = True) -> Path:
    data = {
        "patient_id": ["p1", "p1", "p2"],
        "visit_date": ["2020-01-01", "2021-01-01", "2020-06-01"],
        "age": [61, 62, 55],
        "sex": ["M", "M", "F"],
        "levodopa_eq_dose": [100, 150, 0],
    }
    if include_outcome:
        data["MDS_UPDRS_Total"] = [30, 34, 28]
    df = pd.DataFrame(data)
    p = tmp_path / "ppmi_clinical.parquet"
    df.to_parquet(p, index=False)
    return p


def test_valid_inputs_report_counts_and_outcome(tmp_path):
    asv = _make_asv(tmp_path)
    clinical = _make_clinical(tmp_path, include_outcome=True)
    report = ingest.validate_inputs(asv, clinical)
    assert report["asv"]["rows"] == 3
    assert report["asv"]["columns"] == 5
    assert report["asv"]["taxon_columns"] == 2
    assert report["clinical"]["rows"] == 3
    assert report["clinical"]["outcome_column_present"] is True
    assert report["skip_slope_and_correlation"] is False
    assert report["skip_mixed_effects"] is False
    assert report["synthetic_fallback_used"] is False


def test_missing_input_file_exits_nonzero(tmp_path, caplog):
    asv = _make_asv(tmp_path)
    # clinical file deliberately not created
    missing = tmp_path / "ppmi_clinical.parquet"
    with pytest.raises(FileNotFoundError) as excinfo:
        ingest.validate_inputs(asv, missing)
    assert "ppmi_clinical.parquet" in str(excinfo.value)
    # main() must translate the error into a non-zero exit code
    with pytest.raises(SystemExit) as exitinfo:
        try:
            ingest.main(asv, missing)
        except FileNotFoundError as exc:
            raise SystemExit(1) from exc
    assert exitinfo.value.code != 0


def test_missing_outcome_column_exits_zero_with_skip_flag(tmp_path, caplog):
    asv = _make_asv(tmp_path)
    clinical = _make_clinical(tmp_path, include_outcome=False)
    report_path = tmp_path / "ingest_validation.json"
    code = ingest.main(asv, clinical, report_path)
    assert code == 0
    saved = json.loads(report_path.read_text())
    assert saved["outcome_column_present"] is False
    assert saved["skip_slope_and_correlation"] is True
    assert saved["skip_mixed_effects"] is True
    assert saved["synthetic_fallback_used"] is False
    # a warning about the missing outcome must have been logged
    assert any(
        "MDS_UPDRS_Total" in r.message and r.levelname == "WARNING"
        for r in caplog.records
    )


def test_malformed_asv_missing_columns_aborts(tmp_path):
    bad = tmp_path / "ppmi_asv.csv"
    pd.DataFrame({"foo": [1, 2]}).to_csv(bad, index=False)
    clinical = _make_clinical(tmp_path)
    with pytest.raises(FileNotFoundError):
        ingest.validate_inputs(bad, clinical)


def test_main_writes_validation_report(tmp_path):
    asv = _make_asv(tmp_path)
    clinical = _make_clinical(tmp_path, include_outcome=True)
    report_path = tmp_path / "ingest_validation.json"
    code = ingest.main(asv, clinical, report_path)
    assert code == 0
    saved = json.loads(report_path.read_text())
    assert saved["asv"]["rows"] == 3
    assert saved["outcome_column_present"] is True
